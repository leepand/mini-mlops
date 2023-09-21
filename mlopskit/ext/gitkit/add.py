import os

from .rm import rm
from .hash import object_hash
from .index import index_read, GitIndexEntry, index_write


def add(repo, paths, delete=True, skip_missing=False):

    # First remove all paths from the index, if they exist.
    rm(repo, paths, delete=delete, skip_missing=True)

    worktree = repo.worktree + os.sep

    # Convert the paths to pairs: (absolute, relative_to_worktree).
    # Also delete them from the index if they're present.
    clean_paths = list()
    for path in paths:
        abspath = os.path.abspath(path)
        if not (abspath.startswith(worktree) and os.path.isfile(abspath)):
            raise Exception("Not a file, or outside the worktree: {}".format(paths))
        relpath = os.path.relpath(abspath, repo.worktree)
        clean_paths.append((abspath, relpath))

        # Find and read the index.  It was modified by rm.  (This isn't
        # optimal, good enough for wyag!)
        #
        # @FIXME, though: we could just
        # move the index through commands instead of reading and writing
        # it over again.
        index = index_read(repo)

        for (abspath, relpath) in clean_paths:
            with open(abspath, "rb") as fd:
                sha = object_hash(fd, b"blob", repo)

            stat = os.stat(abspath)

            ctime_s = int(stat.st_ctime)
            ctime_ns = stat.st_ctime_ns % 10**9
            mtime_s = int(stat.st_mtime)
            mtime_ns = stat.st_mtime_ns % 10**9

            entry = GitIndexEntry(
                ctime=(ctime_s, ctime_ns),
                mtime=(mtime_s, mtime_ns),
                dev=stat.st_dev,
                ino=stat.st_ino,
                mode_type=0b1000,
                mode_perms=0o644,
                uid=stat.st_uid,
                gid=stat.st_gid,
                fsize=stat.st_size,
                sha=sha,
                flag_assume_valid=False,
                flag_stage=False,
                name=relpath,
            )
            index.entries.append(entry)

        # Write the index back
        index_write(repo, index)
