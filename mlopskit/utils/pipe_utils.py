import ntpath
import json

# **********************************
# filehash
# **********************************

import hashlib
from mlopskit import make

CENTER_CONFIG =make("config/x")

def filemd5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(int(1e7)), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# **********************************
# copy/move folder
# **********************************
import os
import shutil


def copytree(src, dst, move=False, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        print(s, d)
        if os.path.isdir(s):
            if move:
                shutil.move(s, d)
            else:
                shutil.copytree(s, d, symlinks, ignore)
        else:
            if move:
                shutil.move(s, d)
            else:
                shutil.copy2(s, d)


from pathlib import Path
import warnings


class ConfigManager(object):

    """

    Manage local config. The config is stored in JSON and can be edited directly `filecfg` location, by default '~/d6tpipe/cfg.json'

    Args:
        profile (str): name of profile to use
        filecfg (str): path to where config file is stored

    """

    def __init__(self, profile=None, filecfg="~/mlopskit/cfg.json"):
        self.profile = "default" if profile is None else profile
        if str(filecfg).startswith("~"):
            filecfg = os.path.expanduser(filecfg)
        self.filecfg = filecfg

    def init(self, config=None, server=CENTER_CONFIG["gitserver_remote_url"], reset=False):
        """

        Initialize config with content

        Args:
            config (dict): manually pass config object
            server (str): location of REST API server
            reset (bool): force reset of an existing config

        """

        if (
            os.path.exists(self.filecfg)
            and not reset
            and self.profile in self._loadall()
        ):
            # todo: why does Path(self.filecfg).exists() not work in pytest?
            warnings.warn(
                "Config for profile {} in {} already exists, skipping init. Use reset=True to reset config.".format(
                    self.profile, self.filecfg
                )
            )
            return None

        if not config:
            config = {}
        if "server" not in config:
            config["server"] = server
        if "filerepo" not in config:
            config["filerepo"] = "~/mlopskit"
        p = Path(config["filerepo"])
        p2 = p / "files/{}/".format(self.profile)
        config["filereporoot"] = str(p)
        config["filerepo"] = str(p2)
        if "filedb" not in config:
            config["filedb"] = str(p2 / ".filedb.json")

        # create config file if doesn't exist
        if not os.path.exists(self.filecfg):
            if not os.path.exists(ntpath.dirname(self.filecfg)):
                os.makedirs(ntpath.dirname(self.filecfg))

        self._save(config)

    def update(self, config):
        """

        Update config. Only keys present in the new dict will be updated, other parts of the config will be kept as is. In other words you can pass in a partial dict to update just the parts you need to be updated.

        Args:
            config (dict): updated config

        """

        configall = self._loadall()
        config_current = configall[self.profile]
        config_current.update(config)
        self._save(config_current)
        return True

    def _save(self, config):
        if os.path.exists(self.filecfg):
            configall = self._loadall()
            configall[self.profile] = config
        else:
            configall = {}
        configall[self.profile] = config
        with open(self.filecfg, "w") as f:
            json.dump(configall, f, indent=4)
        return True

    def _loadall(self):
        if not os.path.exists(self.filecfg):
            self.init()
            print(
                'auto created profile "{}", see docs how to customize profile'.format(
                    self.profile
                )
            )
        with open(self.filecfg, "r") as f:
            config = json.load(f)
        return config

    def load(self):
        """

        Loads config

        Returns:
            dict: config

        """

        config = self._loadall()
        if self.profile not in config:
            self.init()
            config = self._loadall()
            warnings.warn(
                'auto created profile "{}", see docs how to customize profile'.format(
                    self.profile
                )
            )
        config = config[self.profile]
        for ikey in ["filereporoot", "filerepo", "filedb"]:
            if config[ikey].startswith("~"):  # do this dynamically
                config[ikey] = os.path.expanduser(config[ikey])
        if not os.path.exists(config["filerepo"]):
            os.makedirs(config["filerepo"])

        return config
