import os, shutil, time, fnmatch, re, copy, itertools
from pathlib import Path, PurePosixPath
import warnings, logging

from mlopskit.ext.tinydb_serialization import SerializationMiddleware
from mlopskit.ext.tinydb_serializers import DateTimeSerializer
from mlopskit.ext.tinydb import TinyDB, Query

from datetime import datetime
from .utils.pipe_utils import filemd5, copytree, ConfigManager
import cachetools
from tqdm import tqdm
from mlopskit.pastry.api.registration import make
from .utils.addict import Dict
from .utils.read_log import LogReader
from mlopskit.pastry.api.colorize import colorize

import time
import subprocess
import traceback


from mlopskit.ext.build_context import prebuild_server
from mlopskit.ext.store import YAMLDataSet

# **********************************
# helpers
# **********************************

_cfg_mode_valid = ["default", "new", "mod", "all"]
_tdbserialization = SerializationMiddleware()
_tdbserialization.register_serializer(DateTimeSerializer(), "TinyDate")


class PullError(Exception):
    pass


class PushError(Exception):
    pass


class ResourceExistsError(Exception):
    pass


def _tinydb_last(db, getkey=None, sortkey="updated_at"):
    if db is None or len(db) == 0:
        return []
    r = sorted(db.all(), key=lambda k: k[sortkey])[-1]
    return r if getkey is None else r.get(getkey)


def _tinydb_insert(db, filessync, filesremote, fileslocal, version):
    if db is not None:
        db.insert(
            {
                "updated_at": datetime.now(),
                "action": "push",
                "sync": filessync,
                "remote": filesremote,
                "local": fileslocal,
                "version": version,
            }
        )


def _files_new(filesfrom, filesto):
    filesfrom = [f["filename"] for f in filesfrom]
    filesto = [f["filename"] for f in filesto]
    return list(set(filesfrom) - set(filesto))


def _files_new_mlflow(filesfrom, filesto):
    filesfrom = [f.name for f in filesfrom]
    filesto = [f.name for f in filesto]
    return list(set(filesfrom) - set(filesto))


def _filenames(list_):
    return [d["filename"] for d in list_]


def _filenames_mlflow(list_):
    return [d.name for d in list_]


def _files_mod(filesfrom, filesto, key="crc"):
    def _tinydb_to_filedate_dict(query):
        return {k: v for (k, v) in [(d["filename"], d[key]) for d in query]}

    filesto = _tinydb_to_filedate_dict(filesto)
    filesfrom = _tinydb_to_filedate_dict(filesfrom)
    if filesto and filesfrom:
        return [k for k, v in filesfrom.items() if v != filesto.get(k, v)]
    else:
        return []


def _files_mod_mlflow(filesfrom, filesto, key="crc"):
    def _tinydb_to_filedate_dict(query):
        return {k: v for (k, v) in [(d.name, d[key]) for d in query]}

    filesto = _tinydb_to_filedate_dict(filesto)
    filesfrom = _tinydb_to_filedate_dict(filesfrom)
    if filesto and filesfrom:
        return [k for k, v in filesfrom.items() if v != filesto.get(k, v)]
    else:
        return []


def _files_sort(files, sortby="filename"):
    return sorted(files, key=lambda k: k[sortby])


def _files_diff(filesfrom, filesto, mode, include, exclude, nrecent=0):
    if nrecent != 0:
        filesfrom_bydate = _files_sort(filesfrom, "modified_at")
        filesfrom = (
            filesfrom_bydate[-nrecent:] if nrecent > 0 else filesfrom_bydate[:nrecent]
        )
    if filesto:
        if mode == "new":
            filesdiff = _files_new(filesfrom, filesto)
        elif mode == "modified":
            filesdiff = _files_mod(filesfrom, filesto)
        elif mode == "default":
            filesdiff = _files_new(filesfrom, filesto) + _files_mod(filesfrom, filesto)
        elif mode == "all":
            filesdiff = _filenames(filesfrom)
        else:
            raise ValueError("Invalid pipe mode")
    else:
        filesdiff = _filenames(filesfrom)

    filesdiff = _apply_fname_filter(filesdiff, include, exclude)

    return filesdiff


def _apply_fname_filter(fnames, include, exclude):
    # todo: multi filter with *.csv|*.xls*|*.txt, split on |
    def helper(list_, filter_):
        return list(
            itertools.chain.from_iterable(
                fnmatch.filter(list_, ifilter) for ifilter in filter_.split("|")
            )
        )

    if include:
        fnames = helper(fnames, include)

    if exclude:
        fnamesex = helper(fnames, exclude)
        fnames = list(set(fnames) - set(fnamesex))

    return fnames


# ************************************************
# Pipe
# ************************************************


class PipeBase(object):
    """

    Abstract class, use the functions but dont instantiate the class

    """

    def __init__(self, name, sortby="filename"):
        # if not re.match(r"^[a-zA-Z0-9-]+$", name):
        #    raise ValueError("Invalid pipe name, needs to be alphanumeric [a-zA-Z0-9-]")
        self.name = name
        self.sortby = sortby

    def _set_dir(self, dir):
        self.filerepo = self.cfg_profile["filerepo"]
        self.dirpath = Path(self.filerepo) / dir
        self.dirpath.mkdir(parents=True, exist_ok=True)  # create dir if doesn't exist
        self.dir = str(self.dirpath) + os.sep

    def _getfilter(self, include=None, exclude=None):
        return include, exclude

    def _files_sort(self, files, sortby=None):
        sortby = self.sortby if sortby is None else sortby
        sortby = "filename" if sortby == "name" else sortby
        sortby = "modified_at" if sortby == "mod" else sortby
        return _files_sort(files, sortby)

    def scan_local(
        self,
        localpath=None,
        filename=None,
        include=None,
        exclude=None,
        attributes=False,
        sortby=None,
        files=None,
        fromdb=False,
        on_not_exist="warn",
    ):
        """

        Get file attributes from local. To run before doing a pull/push

        Args:
            include (str): pattern of files to include, eg `*.csv` or `a-*.csv|b-*.csv`
            exclude (str): pattern of files to exclude
            attributes (bool): return filenames with attributes
            sortby (str): sort files this key. `name`, `mod`, `size`
            files (list): override list of filenames
            fromdb (bool): use files from local db, if false scans all files in pipe folder
            on_not_exist (bool): how to handle missing files when creating file attributes

        Returns:
            list: filenames with attributes

        """

        if files is None:
            if fromdb:
                files = _tinydb_last(self.dbfiles, "local")
                files = _filenames(files)
            else:
                if filename is None:
                    name = self.name
                else:
                    name = filename

                if localpath is None:
                    path_str = os.path.join(os.getcwd(), str(name))
                else:
                    path_str = os.path.join(localpath, str(name))
                dir_path = Path(path_str)

                _dir = str(dir_path) + os.sep

                files = [
                    str(PurePosixPath(p.relative_to(_dir)))
                    for p in dir_path.glob("**/*")
                    if not p.is_dir()
                ]

            include, exclude = self._getfilter(include, exclude)
            files = _apply_fname_filter(files, include, exclude)
        else:
            dir_path = self.local_path_base

        def getattrib(fname, dirpath):
            p = Path(dirpath) / fname
            if not p.exists():
                if on_not_exist == "warn":
                    warnings.warn("Local file {} does not exist".format(fname))
                    return None
            dtmod = datetime.fromtimestamp(p.stat().st_mtime)
            crc = filemd5(p)
            return {
                "filename": fname,
                "modified_at": dtmod,
                "size": p.stat().st_size,
                "crc": crc,
            }

        filesall = [getattrib(fname, dir_path) for fname in files]
        filesall = [o for o in filesall if o is not None]

        filesall = self._files_sort(filesall, sortby)
        if attributes:
            return filesall, files
        else:
            return _filenames(filesall)

    def files(
        self, include=None, exclude=None, sortby=None, check_exists=True, fromdb=True
    ):
        """

        Files synced in local repo

        Args:
            include (str): pattern of files to include, eg `*.csv` or `a-*.csv|b-*.csv`
            exclude (str): pattern of files to exclude
            sortby (str): sort files this key. `name`, `mod`, `size`
            check_exists (bool): check files exist locally

        Returns:
            list: filenames

        """
        return self.filepaths(
            aspath=False,
            include=include,
            exclude=exclude,
            sortby=sortby,
            check_exists=check_exists,
            fromdb=fromdb,
        )

    def filepaths(
        self,
        include=None,
        exclude=None,
        sortby=None,
        check_exists=True,
        aspathlib=True,
        aspath=True,
        fromdb=True,
    ):
        """

        Full path to Files synced in local repo

        Args:
            include (str): pattern of files to include, eg `*.csv` or `a-*.csv|b-*.csv`
            exclude (str): pattern of files to exclude
            sortby (str): sort files this key. `name`, `mod`, `size`
            check_exists (bool): check files exist locally
            aspathlib (bool): return as pathlib object

        Returns:
            path: path to file, either `Pathlib` or `str`

        """

        files = (
            _tinydb_last(self.dbfiles, "local")
            if fromdb
            else self.scan_local(attributes=True)[0]
        )
        files = self._files_sort(files, sortby)
        fnames = _apply_fname_filter(_filenames(files), include, exclude)

        if check_exists:
            [
                FileNotFoundError(fname)
                for fname in fnames
                if not (self.dirpath / fname).exists()
            ]
        if aspath:
            if not aspathlib:
                return [str(self.dirpath / f) for f in fnames]
            else:
                return [self.dirpath / f for f in fnames]
        else:
            return fnames

    def import_files(self, files, subdir=None, move=False):
        """

        Import files to repo

        Args:
            files (list): list of files, eg from `glob.iglob('folder/**/*.csv')`
            subdir (str): sub directory to import into
            move (bool): move or copy

        """
        dstdir = self.dirpath / subdir if subdir else self.dirpath
        dstdir.mkdir(parents=True, exist_ok=True)
        if move:
            [shutil.move(ifile, dstdir / Path(ifile).name) for ifile in files]
        else:
            [shutil.copy(ifile, dstdir / Path(ifile).name) for ifile in files]

    def import_file(self, file, subdir=None, move=False):
        """

        Import a single file to repo

        Args:
            files (str): path to file
            subdir (str): sub directory to import into
            move (bool): move or copy

        """
        self.import_files([file], subdir, move)

    def import_dir(self, dir, move=False):
        """

        Import a directory including subdirs

        Args:
            dir (str): directory
            move (bool): move or copy

        """
        copytree(dir, self.dir, move)

    def delete_files(self, files=None, confirm=True, all_local=None):
        """

        Delete files, local and remote

        Args:
            files (list): filenames, if empty delete all
            confirm (bool): ask user to confirm delete
            all_local (bool): delete all files or just synced files? (local only)

        """
        self.delete_files_remote(files=files, confirm=confirm)
        self.delete_files_local(files=files, confirm=confirm, delete_all=all_local)

    def delete_files_remote(self, version=None, files=None, confirm=True):
        """

        Delete all remote files

        Args:
            files (list): filenames, if empty delete all
            confirm (bool): ask user to confirm delete

        """
        if not files:
            files = "all"
        if confirm:
            c = input(
                "Confirm deleting {} files in {} (y/n)".format(
                    files, self.remote_prefix
                )
            )
            if c == "n":
                return None
        else:
            c = "y"
        if c == "y":
            if files == "all":
                if version is not None:
                    if isinstance(version, int):
                        version = f"v{version}"
                files = self.scan_remote(version=version, cached=False)
            results = self._pullpush(files, version=version, op="remove")
            return results

    def delete_files_local(
        self, files=None, confirm=True, delete_all=None, ignore_errors=False
    ):
        """

        Delete all local files and reset file database

        Args:
            files (list): filenames, if empty delete all
            confirm (bool): ask user to confirm delete
            delete_all (bool): delete all files or just synced files?
            ignore_errors (bool): ignore missing file errors

        """
        if not files:
            files = "all"
        if confirm:
            c = input("Confirm deleting {} files in {} (y/n)".format(files, self.dir))
            if c == "n":
                return None
        else:
            c = "y"
        if files == "all" and delete_all is None:
            d = input("Delete all files or just downloaded files (a/d)")
            delete_all = True if d == "a" else False
        if c == "y":
            if delete_all:
                shutil.rmtree(self.dir, ignore_errors=ignore_errors)
            else:
                [f.unlink() for f in self.filepaths()]
            self.dbfiles.purge()


class PipeLocal(PipeBase):
    """

    Managed data pipe, LOCAL mode for accessing local files ONLY

    Args:
        api (obj): API manager object
        name (str): name of the data pipe
        profile (str): name of profile to use
        filecfg (str): path to where config file is stored
        sortby (str): sort files this key. `name`, `mod`, `size`

    """

    def __init__(
        self,
        name,
        config=None,
        profile="dev",
        filecfg="~/mlopskit/cfg.json",
        sortby="filename",
    ):
        super().__init__(name, sortby)
        self.profile = "default" if profile is None else profile
        if config is None:
            self.configmgr = ConfigManager(filecfg=filecfg, profile=self.profile)
            self.config = self.configmgr.load()
        else:
            self.config = config
            warnings.warn(
                "Using manual config override, some api functions might not work"
            )

        self.cfg_profile = self.config
        self._set_dir(self.name)

        # create db connection
        self._db = TinyDB(self.cfg_profile["filedb"], storage=_tdbserialization)
        self.dbfiles = self._db.table(name + "-files")
        self.dbconfig = self._db.table(name + "-cfg")

        self.settings = self.dbconfig.all()[-1]["pipe"] if self.dbconfig.all() else {}
        self.schema = self.settings.get("schema", {})

        print(
            "Operating in local mode, use this to access local files, to run remote operations use `Pipe()`"
        )


class Pipe(PipeBase):
    """
    Managed data pipe

    Args:
        api (obj): API manager object
        name (str): name of the data pipe. Has to be created first
        mode (str): sync mode
        sortby (str): sort files this key. `name`, `mod`, `size`
        credentials (dict): override credentials

    Note:
        * mode: controls which files are synced
            * 'default': modified and new files
            * 'new': new files only
            * 'mod': modified files only
            * 'all': all files

    """

    def __init__(
        self,
        name,
        mode="default",
        sortby="filename",
        remotepath=None,
        config=None,
        profile=None,
        filecfg="~/mlopskit/cfg.json",
        credentials=None,
    ):
        # set params
        super().__init__(name, sortby)
        self.profile = "default" if profile is None else profile
        if config is None:
            self.configmgr = ConfigManager(filecfg=filecfg, profile=self.profile)
            self.config = self.configmgr.load()
        else:
            self.config = config
            warnings.warn(
                "Using manual config override, some api functions might not work"
            )

        # self.api_islocal = api.__class__.__name__ == "APILocal"
        if not mode in _cfg_mode_valid:
            raise ValueError("Invalid mode, needs to be {}".format(_cfg_mode_valid))
        self.mode = mode

        # get remote details
        # self.cnxnapi = api.cnxn
        # self.cnxnpipe = self.cnxnapi.pipes._(name)
        # self.settings = self.cnxnpipe.get()[1]
        self.settings = {"protocol": "s3", "options": {}}
        if not self.settings:
            raise ValueError("pipe not found, make sure it was created")
        if self.settings["protocol"] not in ["s3", "ftp", "sftp"]:
            raise NotImplementedError(
                "Unsupported protocol, only s3 and (s)ftp supported"
            )
        self.settings["options"] = self.settings.get("options", {})
        self.settings["options"]["remotepath"] = remotepath
        self.remote_prefix = self.settings["options"]["remotepath"]
        self.encrypted_pipe = self.settings["options"].get("encrypted", False)
        if self.encrypted_pipe:
            self.settings = self.api.decode(self.settings)
        self.role = self.settings.get("role")
        self.cfg_profile = self.config
        self._set_dir(self.name)
        self.credentials_override = credentials

        # DDL
        self.schema = self.settings.get("schema", {})

        # create db connection
        self._db = TinyDB(self.cfg_profile["filedb"], storage=_tdbserialization)
        self.dbfiles = self._db.table(name + "-files")
        self.dbconfig = self._db.table(name + "-cfg")

        self._cache_scan = cachetools.TTLCache(maxsize=1, ttl=5 * 60)
        self.mlflow_client = make("client").mlflow_client
        self.mlflow_art_path = make("config/model")["mlflow_art_path"]

        # connect msg
        msg = "Successfully connected to pipe {}. ".format(self.name)
        if self.role == "read":
            msg += " Read only access"
        print(msg)
        self.dbconfig.upsert(
            {"name": self.name, "pipe": self.settings}, Query().name == self.name
        )

    def _getfilter(self, include, exclude):
        if include is None:
            include = self.settings["options"].get("include")
        if exclude is None:
            exclude = self.settings["options"].get("exclude")
        return include, exclude

    def setmode(self, mode):
        """

        Set sync mode

        Args:
            mode (str): sync mode

        Note:
            * mode: controls which files are synced
                * 'default': modified and new files
                * 'new': new files only
                * 'mod': modified files only
                * 'all': all files

        """
        assert mode in _cfg_mode_valid
        self.mode = mode

    def update_settings(self, settings):
        """

        Update settings. Only keys present in the new dict will be updated, other parts of the config will be kept as is. In other words you can pass in a partial dict to update just the parts you need to be updated.

        Args:
            config (dict): updated config

        """

        self.settings.update(settings)
        response, data = self.cnxnpipe.patch(self.settings)
        return response, data

    def list_model_versions(self, model_name=None, return_type="all"):
        if model_name is None:
            model_name = self.name
        if return_type == "version":
            return [
                v.version for v in self.mlflow_client.list_model_versions(model_name)
            ]
        elif return_type == "stage":
            return [v.stage for v in self.mlflow_client.list_model_versions(model_name)]
        elif return_type == "desc":
            return [
                v.description
                for v in self.mlflow_client.list_model_versions(model_name)
            ]
        else:
            return [v for v in self.mlflow_client.list_model_versions(model_name)]

    def list_models(self, names_only=True, parent_only=False):
        """

        List all models you have access to

        Args:
            names_only (bool): if false, return all details

        """
        r = self.mlflow_client.list_models()
        if names_only:
            r = sorted(_filenames_mlflow(r))

        return r

    def list_prod_models(self, attributes=False, cached=True):
        """

        Get file attributes from remote. To run before doing a pull/push

        Args:
            cached (bool): use cached results

        Returns:
            list: filenames with attributes in remote

        """

        c = self._cache_scan.get(0)
        if cached and c is not None:
            response, data = c
        else:
            filenames = self.mlflow_client.list_models()
            response, data = (
                (),
                filenames,
            )  # REST API style, for future to return from API
            self._cache_scan[0] = (response, data)

        if attributes:
            return response, data
        else:
            return _filenames_mlflow(data)

    def scan_remote(self, version=None, attributes=False, cached=False):
        """

        Get file attributes from remote. To run before doing a pull/push

        Args:
            version (str): if not version will return all versions
            cached (bool): use cached results

        Returns:
            list: filenames with attributes in remote

        """

        c = self._cache_scan.get(0)
        if cached and c is not None:
            response, data = c
        else:
            if version is not None:
                if isinstance(version, int):
                    version = f"v{version}"
                dirpath = self.dirpath / str(version)
                _dir = str(dirpath) + os.sep
            else:
                dirpath = self.dirpath
                _dir = self.dir
            files = [
                str(PurePosixPath(p.relative_to(_dir)))
                for p in dirpath.glob("**/*")
                if not p.is_dir()
            ]

            def getattrib(fname, dir_path):
                on_not_exist = "warn"
                p = Path(dir_path) / fname
                if not p.exists():
                    if on_not_exist == "warn":
                        warnings.warn("Local file {} does not exist".format(fname))
                        return None
                dtmod = datetime.fromtimestamp(p.stat().st_mtime)
                crc = filemd5(p)
                return {
                    "filename": fname,
                    "modified_at": dtmod,
                    "size": p.stat().st_size,
                    "crc": crc,
                }

            filesall = [getattrib(fname, dirpath) for fname in files]
            filesall = [o for o in filesall if o is not None]

        if attributes:
            return filesall, files
        else:
            return _filenames(filesall)

    def is_synced(self, israise=False):
        """

        Check if local is in sync with remote

        Args:
            israise (bool): raise an exception

        Returns:
            bool: pipe is updated

        """

        filespull = self.pull(dryrun=True)
        if filespull:
            if israise:
                raise PushError(
                    [
                        "Remote has changes not pulled to local repo, run pull first",
                        filespull,
                    ]
                )
            else:
                return False
        return True

    def pull_preview(
        self, version=None, include=None, exclude=None, nrecent=0, cached=True
    ):
        """

        Preview of files to be pulled

        Args:
            files (list): override list of filenames
            include (str): pattern of files to include, eg `*.csv` or `a-*.csv|b-*.csv`
            exclude (str): pattern of files to exclude
            nrecent (int): use n newest files by mod date. 0 uses all files. Negative number uses n old files
            cached (bool): if True, use cached remote information, default 5mins. If False forces remote scan

        Returns:
            list: filenames with attributes

        """

        return self.pull(
            version=version,
            dryrun=True,
            include=include,
            exclude=exclude,
            nrecent=nrecent,
            cached=cached,
        )

    def pull(
        self,
        files=None,
        dryrun=False,
        version=None,
        include=None,
        exclude=None,
        nrecent=0,
        merge_mode=None,
        cached=True,
    ):
        """

        Pull remote files to local

        Args:
            files (list): override list of filenames
            dryrun (bool): preview only
            include (str): pattern of files to include, eg `*.csv` or `a-*.csv|b-*.csv`
            exclude (str): pattern of files to exclude
            nrecent (int): use n newest files by mod date. 0 uses all files. Negative number uses n old files
            merge_mode (str): how to deal with pull conflicts ie files that changed both locally and remotely? 'keep' local files or 'overwrite' local files
            cached (bool): if True, use cached remote information, default 5mins. If False forces remote scan

        Returns:
            list: filenames with attributes

        """

        if not cached:
            self._cache_scan.clear()

        if version is None:
            latest_version = self.mlflow_client.list_model_versions(
                self.name, "Production"
            )
            if len(latest_version) > 0:
                version = f"v{latest_version[0].version}"
            else:
                version = "v1"
        else:
            if isinstance(version, int):
                version = f"v{version}"
            else:
                version = version

        filesremote = self.scan_remote(version, attributes=True)[0]

        if files is not None:
            filespull = files
        else:
            logging.debug(["pull remote files", version])
            filesdiff = _filenames(filesremote)
            filespull = _apply_fname_filter(filesdiff, include, exclude)

        filespull_size = sum(
            f["size"] for f in filesremote if f["filename"] in filespull
        )
        print("pulling: {:.2f}MB".format(filespull_size / 2**20))
        if dryrun:
            return filespull

        filessync = self._pullpush(filespull, version, "get")

        # scan local files after pull
        fileslocal, _ = self.scan_local(files=filessync, attributes=True)
        # update db
        _tinydb_insert(self.dbfiles, filessync, filesremote, fileslocal, version)
        self.dbconfig.upsert(
            {"name": self.name, "remote": self.settings, "pipe": self.settings},
            Query().name == self.name,
        )

        return filessync

    def push_preview(self, include=None, exclude=None, nrecent=0, cached=True):
        """

        Preview of files to be pushed

        Args:
            files (list): override list of filenames
            include (str): pattern of files to include, eg `*.csv` or `a-*.csv|b-*.csv`
            exclude (str): pattern of files to exclude
            nrecent (int): use n newest files by mod date. 0 uses all files. Negative number uses n old files
            cached (bool): if True, use cached remote information, default 5mins. If False forces remote scan

        Returns:
            list: filenames with attributes

        """

        return self.push(
            dryrun=True,
            include=include,
            exclude=exclude,
            nrecent=nrecent,
            cached=cached,
        )

    def push(
        self,
        files=None,
        version=None,
        localpath=None,
        filename=None,
        dryrun=False,
        fromdb=False,
        to_remote=True,
        include=None,
        exclude=None,
        nrecent=0,
        cached=True,
    ):
        """

        Push local files to remote

        Args:
            files (list): override list of filenames
            dryrun (bool): preview only
            fromdb (bool): use files from local db, if false scans all files in pipe folder
            include (str): pattern of files to include, eg `*.csv` or `a-*.csv|b-*.csv`
            exclude (str): pattern of files to exclude
            nrecent (int): use n newest files by mod date. 0 uses all files. Negative number uses n old files
            cached (bool): if True, use cached remote information, default 5mins. If False forces remote scan

        Returns:
            list: filenames with attributes

        """

        self._has_write()

        if not cached:
            self._cache_scan.clear()

        if filename is None:
            name = self.name
        else:
            name = filename

        if localpath is None:
            path_str = os.path.join(os.getcwd(), str(name))
        else:
            path_str = os.path.join(localpath, str(name))
        dir_path = Path(path_str)

        _dir = str(dir_path) + os.sep
        # self.model_files_to_push = str(dir_path)
        self.model_files_to_push = filename
        _fileslocal = [
            str(PurePosixPath(p.relative_to(_dir)))
            for p in dir_path.glob("**/*")
            if not p.is_dir()
        ]

        def getattrib(fname, dirpath):
            p = Path(dirpath) / fname
            if not p.exists():
                on_not_exist = "warn"
                if on_not_exist == "warn":
                    warnings.warn("Local file {} does not exist".format(fname))
                    return None
            dtmod = datetime.fromtimestamp(p.stat().st_mtime)
            crc = filemd5(p)
            return {
                "filename": fname,
                "modified_at": dtmod,
                "size": p.stat().st_size,
                "crc": crc,
            }

        if files is not None:
            filespush = files
            filesall = [getattrib(fname, dir_path) for fname in files]
            fileslocal = [o for o in filesall if o is not None]

        else:
            filespush = _fileslocal
            filesall = [getattrib(fname, dir_path) for fname in _fileslocal]
            fileslocal = [o for o in filesall if o is not None]

        if version is None:
            latest_version = self.mlflow_client.list_model_versions(
                self.name, "Production"
            )
            if len(latest_version) > 0:
                version = f"v{latest_version[0].version}"
            else:
                version = "v1"
        else:
            if isinstance(version, int):
                version = f"v{version}"
            else:
                version = version

        include, exclude = self._getfilter(include, exclude)
        files = _apply_fname_filter(filespush, include, exclude)

        filespush_size = sum(f["size"] for f in fileslocal if f["filename"] in files)
        print("pushing: {:.2f}MB".format(filespush_size / 2**20))
        if dryrun:
            return files

        filessync = self._pullpush(
            files, version=version, op="put", push_to_remote=to_remote
        )

        # get files on remote after push
        filesremote = self.scan_remote(version=version, cached=False, attributes=True)[
            1
        ]
        _tinydb_insert(self.dbfiles, filessync, filesremote, fileslocal, version)

        return filessync

    def reset(self, delete=False):
        """
        Resets by deleting all files and pulling
        """

        if delete:
            self.delete_files_local()
        self.setmode("all")
        self.pull(cached=False)
        self.setmode("default")

    def remove_files(self, version=None, files=None, direction="remote", dryrun=None):
        """

        Remove file orphans locally and/or remotely. When you remove files, they don't get synced because pull/push only looks at new or modified files. Use this to clean up any removed files.

        Args:
            direction (str): where to remove files
            dryrun (bool): preview only

        Note:
            * direction:
                * 'local': remove files locally, ie files that exist on local but not in remote
                * 'remote': remove files remotely, ie files that exist on remote but not in local
                * 'both': combine local and remote

        """

        assert direction in ["both", "local", "remote"]
        if dryrun is None:
            warnings.warn(
                "dryrun active by default, to execute explicitly pass dryrun=False"
            )
            dryrun = True

        if version is None:
            warnings.warn("to execute explicitly pass version=x x is int")
            return
        _ver = f"v{version}"

        if files is None:
            filesremote = self.scan_remote(version=_ver, attributes=True)[1]

            filesrmremote = []

            if direction in ["remote", "both"]:
                self._has_write()
                filesrmremote = filesremote
        else:
            filesrmremote = files

        if dryrun:
            return {"remote": filesrmremote}

        for fname in filesrmremote:
            try:
                # (self.dirpath / version / fname).unlink()
                file_path = str(self.dirpath / _ver / fname)
                print(file_path, "file_path")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    # print(f"The file '{file_path}' has been deleted.")
                else:
                    print(f"The file '{file_path}' does not exist.")
            except:
                warnings.warn(f"Unable to delete file {fname},{traceback.format_exc()}")

        return {"remote": filesrmremote}

    def _has_write(self):
        if self.role == "read":
            raise ValueError("Read-only role, cannot write")

    def _get_credentials(self, write=False):
        action = "write" if write else "read"

        # check role
        if write:
            self._has_write()

        # get credentials from api
        if self.api_islocal:
            credentials = self.cnxnpipe.get()[1]["credentials"]
            if "read" in credentials:
                credentials = credentials[action]
            if "key" in credentials:
                credentials["aws_access_key_id"] = credentials.pop("key")
            if "secret" in credentials:
                credentials["aws_secret_access_key"] = credentials.pop("secret")
        else:
            credentials = self.cnxnpipe.credentials.get(query_params={"role": action})[
                1
            ]
        if not credentials:
            raise ValueError(
                "No {} credentials provided, make sure pipe has credentials. ".format(
                    "write" if write else "read"
                )
            )
        return credentials

    def _reset_credentials(self):
        self.cnxnpipe.credentials.get(query_params={"role": "read", "renew": True})

    def _connect(self, write=False):
        credentials = self._get_credentials(write)
        if self.settings["protocol"] == "s3":
            from luigi.contrib.s3 import S3Client
            from d6tpipe.luigi.s3 import S3Client as S3ClientToken

            if write:
                if "aws_session_token" in credentials:
                    cnxn = S3ClientToken(**credentials)
                else:
                    cnxn = S3Client(**credentials)
            else:
                if "aws_session_token" in credentials:
                    cnxn = S3ClientToken(**credentials)
                else:
                    cnxn = S3Client(**credentials)

        else:
            raise NotImplementedError("only s3 and ftp supported")

        return cnxn

    def _disconnect(self, cnxn):
        if self.settings["protocol"] == "ftp":
            cnxn.close_del()

    def _pullpush(self, files, version=None, op="get", push_to_remote=False, cnxn=None):
        # if cnxn is None:
        #    cnxn = self._connect(op in ['put','remove'])

        filessync = []
        pbar = ""
        # upload files to mlops remote space
        if push_to_remote:
            make(
                f"model/{self.name}-{version}",
                to_push_file=self.model_files_to_push,
            )
        for fname in tqdm(files):
            pbar = pbar + fname
            fnameremote = self.mlflow_art_path + fname
            fnamelocalpath = self.dirpath / fname
            fnamelocal = str(PurePosixPath(fnamelocalpath))
            if op == "put":
                # upload file to code repos
                _fnamelocalpath = Path(
                    os.path.join(str(PurePosixPath(self.dirpath)), f"{version}/{fname}")
                )
                _fnamelocalpath.parent.mkdir(parents=True, exist_ok=True)
                new_file = os.path.join(
                    str(PurePosixPath(self.dirpath)), f"{version}/{fname}"
                )
                shutil.copy(os.path.join(self.model_files_to_push, fname), new_file)

                # cnxn.put(fnamelocal, fnameremote)
            elif op == "get":
                _fnamelocalpath = Path(
                    os.path.join(os.getcwd(), f"{self.name}/{version}/{fname}")
                )
                _fnamelocalpath.parent.mkdir(parents=True, exist_ok=True)
                # copytree(fnamelocalpath,_fnamelocalpath,move=False)
                new_file = f"{os.getcwd()}/{self.name}/{version}/{fname}"
                self.local_path_base = f"{os.getcwd()}/{self.name}/{version}"
                remote_path_file = self.dirpath / version / fname
                shutil.copy(remote_path_file, new_file)

            elif op == "remove":
                try:
                    _ver = version
                    file_path = str(self.dirpath / _ver / fname)
                    os.remove(file_path)
                except:
                    warnings.warn("Unable to delete remote file {}".format(fnameremote))
            elif op == "exists":
                fname = cnxn.exists(fnameremote)
            else:
                raise ValueError("invalid luigi operation")

            logging.info("synced files {}".format(fname))
            filessync.append(fname)

        # self._disconnect(cnxn)

        return filessync

    def get_prodction_version(self):
        pass


class ServingMgr:
    def __init__(self, models, mode="new"):
        self.models = models
        self.pipes = []
        for model in models:
            self.pipes.append(Pipe(name=model, mode=mode))

    def get_service_info(self):
        path_all = []
        prod_versions = []
        info_all = {}
        for pipe in self.pipes:
            # path_all.append(pipe.dir)
            info = {}

            latest_version = pipe.mlflow_client.list_model_versions(
                pipe.name, "Production"
            )
            if len(latest_version) > 0:
                version = f"v{latest_version[0].version}"
            else:
                version = f"v1"

            info["prodction_version"] = version
            info["model_main_path"] = pipe.dir
            port_info = make(f"meta/{pipe.name}")
            info["port_info"] = port_info
            info_all[pipe.name] = info

            # prod_versions.append(f"{pipe.name}:{version}")
        return info_all
        # return path_all, prod_versions

    def start_service(self, kill_or_start="all"):
        service_msg = Dict()
        for pipe in self.pipes:
            latest_version = pipe.mlflow_client.list_model_versions(
                pipe.name, "Production"
            )
            if len(latest_version) > 0:
                version = f"v{latest_version[0].version}"
            else:
                if isinstance(version, int):
                    version = f"v{version}"
                else:
                    version = version

            prod_path = os.path.join(pipe.dir, version)
            if_dir = Path(prod_path).is_dir()
            status = "stoped"
            # msg = ""
            if not if_dir:
                # msg = "生产路径不存在"
                status = "no_code_path"
            # service_msg[pipe.name]["msg"] = msg
            service_msg[pipe.name]["status"] = status
            make_msg = start_service_bymake(main_code_path=prod_path)
            service_msg[pipe.name]["make_msg"] = make_msg

        return service_msg

    def check_service_status(self):
        msg_status = Dict()
        for pipe in self.pipes:
            port_info = make(f"meta/{pipe.name}")
            recomserver_port = port_info.get("recomserver_port")
            rewardserver_port = port_info.get("rewardserver_port")
            if recomserver_port is None:
                recomserver_status = "not_reg"
            else:
                recomserver_status = "stoped"
            if rewardserver_port is None:
                rewardserver_status = "not_reg"
            else:
                rewardserver_status = "stoped"
            if recomserver_status == "stoped":
                recomserver_status = get_port_status(recomserver_port)
            if rewardserver_status == "stoped":
                rewardserver_status = get_port_status(rewardserver_port)
            msg_status[pipe.name]["recomserver_status"] = recomserver_status
            msg_status[pipe.name]["rewardserver_status"] = rewardserver_status

        return msg_status


def get_port_status(port):
    try:
        process = subprocess.run(
            ["lsof", "-i", f":{str(port)}"],
            capture_output=True,
            preexec_fn=os.setsid,
            text=True,
            check=True,
        )
        stdout = process.stdout
        stderr = process.stderr

        if "PID" in stdout:
            status = "running"
        else:
            status = "failed"

        if stderr:
            status = stderr.strip()

        return status
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


def start_service_bymake(main_code_path):
    try:
        # 执行shell命令并捕获日志
        process = subprocess.run(
            f"cd {main_code_path} && make ksall",
            shell=True,
            capture_output=True,
            preexec_fn=os.setsid,
            text=True,
            timeout=1,  # 设定超时时间
            check=True,  # 检查命令执行结果，若返回非零状态码则抛出异常
        )

        if process.stdout or process.stderr:
            msg = process.stderr.strip()
        else:
            msg = "your script is processed success"

        return msg
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
    except subprocess.TimeoutExpired:
        return "Command execution timed out"


class ServiceMgr:
    def __init__(self, models, env="dev") -> None:
        self.pipes = []
        self.env = env
        self.config_file_name = f"server_{env}.yml"
        for model in models:
            self.pipes.append(Pipe(name=model, profile=env))

    def start_service(self):
        service_msg = Dict()
        for pipe in self.pipes:
            latest_version = pipe.mlflow_client.list_model_versions(
                pipe.name, "Production"
            )
            if len(latest_version) > 0:
                version = f"v{latest_version[0].version}"
            else:
                model_ver = pipe.mlflow_client.list_model_versions(pipe.name)
                if len(model_ver) > 0:
                    v = model_ver[0]
                    version = f"v{v}"
                else:
                    logging.error(f"no version found of {pipe.name}")
                    continue

            prod_path = os.path.join(pipe.dir, version)
            if_dir = Path(prod_path).is_dir()
            status = "stoped"
            # msg = ""
            if not if_dir:
                # msg = "生产路径不存在"
                status = "no_code_path"
                logging.error(f"no_code_path of {pipe.name}")
                continue
            # service_msg[pipe.name]["msg"] = msg
            # service_msg[pipe.name]["status"] = status
            config_file = os.path.join(prod_path, "config", self.config_file_name)
            config = YAMLDataSet(config_file).load()
            ops_servers = config.get("ops_servers", ["recomserver", "rewardserver"])
            for ops_server in ops_servers:
                ops_server_config = config[ops_server]
                server_name = ops_server_config["server_name"]
                ports = ops_server_config["ports"]
                serving = ops_server_config["serving"]
                workers = ops_server_config["workers"]
                _prebuild_path = ops_server_config.get("prebuild_path", "src")

                prebuild_path = os.path.join(prod_path, _prebuild_path)
                make_msg = prebuild_server(
                    prebuild_path,
                    server_name,
                    ports,
                    workers=workers,
                    serving=serving,
                    model_name=pipe.name,
                )

            # make_msg = start_service_bymake(main_code_path=prod_path)
            service_msg[pipe.name]["msg"] = make_msg

        return service_msg

    def scan_logs(self, buffer_size=8192):
        for pipe in self.pipes:
            latest_version = pipe.mlflow_client.list_model_versions(
                pipe.name, "Production"
            )
            if len(latest_version) > 0:
                version = f"v{latest_version[0].version}"
            else:
                model_ver = pipe.mlflow_client.list_model_versions(pipe.name)
                if len(model_ver) > 0:
                    v = model_ver[0]
                    version = f"v{v}"
                else:
                    logging.error(f"no version found of {pipe.name}")
                    continue

            log_path = os.path.join(pipe.dir, version, "logs")
            logs = Path(log_path).glob("*.log")
            # if_dir = Path(prod_path).is_dir()
            for _log in logs:
                log = LogReader(_log, buffer_size=buffer_size)
                print(colorize(_log, "yellow", True, True), "\n", log.read())


# mlflow_client =make("client")
def get_production_model(name):
    try:
        mlflow_client = make("client").mlflow_client
        # This will fetch all registered models
        prod = [
            model
            for model in mlflow_client.search_model_versions(f"name='{name}'")
            if str(model.stage) == "ModelVersionStage.PROD"
        ]
        model = prod[0]
        print(f"Run_ID: {model.run_id}")
        print(f"Model Name: {model.name}")
        print(f"Version: {model.version}")
    except:
        print("No Production Model Found")