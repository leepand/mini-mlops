import mlopskit.ext.shellkit as sh
from mlopskit.ext.dpipe import api, pipe
from .math_util import is_number

import os


def git_pipe_gen(name, version, profile):
    # paths = list(sh.walkfiles())
    if name == "0":
        local_model_name = sh.read(".name")
        model_name = local_model_name
    else:
        model_name = name

    if version == "0":
        local_model_version = sh.read(".version")
        if is_number(local_model_version):
            model_version = f"v{local_model_version}"
        else:
            model_version = version
    else:
        model_version = version

    model_path = os.path.join(name, version)
    sh.mkdir(model_path)
    _api = api.APIClient(profile=profile)
    # pull files from a data pipe
    _pipe = pipe.Pipe(
        _api, name=model_name, version=model_version
    )  # connect to a data pipe

    return _pipe, model_name, model_version
