from __future__ import annotations
from typing import Protocol, runtime_checkable
import aiofiles
import shutil
import logging
from fastapi import UploadFile, HTTPException
import os
import subprocess
import time
import datetime

import contextlib
import pathlib
from pathlib import Path

from typing import (
    IO,
    Any,
    Dict,
    Generator,
    Optional,
    Set,
    Type,
    Union,
)

PathLike = Union[str, os.PathLike]

log = logging.getLogger("mlops")


@runtime_checkable
class Model(Protocol):
    def predict(self, features: dict):
        ...


@runtime_checkable
class Featurizer(Protocol):
    def featurize(self, event: dict):
        ...


@runtime_checkable
class Learner(Protocol):
    def learn(self, features: dict, label: str):
        ...


async def save_file(file: UploadFile, filestore: str) -> str:
    """
    Saves the file to the filestore location.
    :param file: The temporary spooled file-like object.
    :param filestore: The location to where the file will be saved.
    :return: filename
    """
    try:
        # async with aiofiles.open(os.path.join(filestore, file.filename), "wb") as f:
        async with aiofiles.open(filestore, "wb") as f:

            # Read the data in chunks and save it, as we go.
            for i in iter(lambda: file.file.read(1024 * 1024 * 64), b""):

                # We can improve this by keeping track of the chunks saved,
                # report that number with an API endpoint and have the client
                # start the upload from the last saved chunk if the upload was
                # interrupted intentionally or due to a network failure.
                await f.write(i)
        log.info(f"File saved as {file.filename}")
    except Exception as e:

        # Not trying to cover all possible errors here, just bubble up the details.
        # Response format based on https://datatracker.ietf.org/doc/html/rfc7807
        problem_response = {"type": str(type(e).__name__), "details": str(e)}
        headers = {"Content-Type": "application/problem+json"}
        log.error(problem_response)
        raise HTTPException(status_code=500, detail=problem_response, headers=headers)
    return file.filename


def make_containing_dirs(path):
    """
    Create the base directory for a given file path if it does not exist; also creates parent
    directories.
    """
    dir_name = os.path.dirname(path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def make_zip(from_dir, to_dir):
    # from_dir = "model_store"
    # to_dir = "save_dir/model_store"
    shutil.make_archive(to_dir, "zip", from_dir)
    return True


def unzip(filename, to_dir):
    # to_dir = "save_dir/model_store"
    # filename = "save_dir/model_store.zip"
    shutil.unpack_archive(filename, to_dir)
    return True


def timeout_command(command, timeout=60):
    start = datetime.datetime.now()
    process = subprocess.Popen(
        command,
        bufsize=1000,
        shell=True,
        stdout=subprocess.PIPE,
        close_fds=True,
        preexec_fn=os.setpgrp,
    )
    while process.poll() is None:
        time.sleep(0.1)
        now = datetime.datetime.now()
        if (now - start).seconds > timeout:
            try:
                process.terminate()
            except Exception as e:
                return None
        return None
    out = process.communicate()[0]
    if process.stdin:
        process.stdin.close()
    if process.stdout:
        process.stdout.close()
    if process.stderr:
        process.stderr.close()
    try:
        process.kill()
    except OSError:
        pass
    return out


@contextlib.contextmanager
def fsync_open(
    path: Union[pathlib.Path, str], mode: str = "w", encoding: Optional[str] = None
) -> Generator[IO[Any], None, None]:
    """
    Opens a path for I/O, guaranteeing that the file is flushed and
    fsynced when the file's context expires.
    """
    with open(path, mode, encoding=encoding) as f:
        yield f

        f.flush()
        os.fsync(f.fileno())


StrPath = Union[str, "os.PathLike[str]"]


def mkdir_exists_ok(dir_name: StrPath) -> None:
    """Create `dir_name` and any parent directories if they don't exist.
    Raises:
        FileExistsError: if `dir_name` exists and is not a directory.
        PermissionError: if `dir_name` is not writable.
    """
    try:
        os.makedirs(dir_name, exist_ok=True)
    except FileExistsError as e:
        raise FileExistsError(f"{dir_name!s} exists and is not a directory") from e
    except PermissionError as e:
        raise PermissionError(f"{dir_name!s} is not writable") from e


def create_file(path: PathLike, content: str, pretend=False, encoding="utf-8"):
    """Create a file in the given path.
    This function reports the operation in the logs.
    Args:
        path: path in the file system where contents will be written.
        content: what will be written.
        pretend (bool): false by default. File is not written when pretending,
            but operation is logged.
    Returns:
        Path: given path
    """
    path = Path(path)
    if not pretend:
        path.write_text(content, encoding=encoding)

    # logger.report("create", path)
    return path


def create_structure(project_main_dir, project_name, model_name, version):
    structure = {
        "README.md": {
            "content": README.substitute(new_proj=project_name),
            "is_dir": False,
        },
        "Makefile": {"content": MAKEFILE, "is_dir": False},
        "tests": {"content": "", "is_dir": True},
        "notebooks": {"content": "", "is_dir": True},
        "config": {"content": "", "is_dir": True},
        "db": {"content": "", "is_dir": True},
        "src/recomserver.py": {
            "content": RECOMSERVER.substitute(name=model_name, version=version),
            "is_dir": False,
            "rel_path": "src",
        },
        "src/rewardserver.py": {
            "content": REWARDSERVER.substitute(name=model_name, version=version),
            "is_dir": False,
            "rel_path": "src",
        },
        "bin/kill_recom.py": {"content": KILLPORT, "is_dir": False, "rel_path": "bin"},
        "bin/kill_reward.py": {"content": KILLPORT, "is_dir": False, "rel_path": "bin"},
        "bin/run_reward.sh": {
            "content": RUN_REWARD,
            "is_dir": False,
            "rel_path": "bin",
        },
        "bin/run_recom.sh": {"content": RUN_RECOM, "is_dir": False, "rel_path": "bin"},
    }
    for file_name, _content in structure.items():
        if _content.get("rel_path"):
            rel_path = _content.get("rel_path")
            content = _content.get("content")
            file_dir = os.path.join(project_main_dir, rel_path)
            os.makedirs(file_dir, exist_ok=True)
            create_file(os.path.join(project_main_dir, file_name), content)
        else:
            if _content.get("is_dir"):
                os.makedirs(os.path.join(project_main_dir, file_name), exist_ok=True)
            else:
                content = _content.get("content")
                create_file(os.path.join(project_main_dir, file_name), content)
