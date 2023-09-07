import importlib
import importlib.util
import sys
import re
import os
from dataclasses import dataclass, field
from .client import HTTPClient
from .util import create_structure

# from mlopskit.utils import logger
from .colorize import colorize
import json
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    SupportsFloat,
    Tuple,
    Union,
    overload,
)

import datetime
import pytz

from mlopskit.pastry.api import error

if sys.version_info < (3, 10):
    import importlib_metadata as metadata  # type: ignore
else:
    import importlib.metadata as metadata

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

ENV_ID_RE = re.compile(
    r"^(?:(?P<namespace>[\w:-]+)\/)?(?:(?P<name>[\w:.-]+?))(?:-v(?P<version>\d+))?$"
)

from structlog import get_logger

logger = get_logger(__name__)


def load(name: str) -> callable:
    """Loads an environment with name and returns an environment creation function
    Args:
        name: The environment name
    Returns:
        Calls the environment constructor
    """
    mod_name, attr_name = name.split(":")
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, attr_name)
    return fn


def parse_env_id(id: str) -> Tuple[Optional[str], str, Optional[int]]:
    """Parse environment ID string format.
    This format is true today, but it's *not* an official spec.
    [namespace/](env-name)-v(version)    env-name is group 1, version is group 2
    2016-10-31: We're experimentally expanding the environment ID format
    to include an optional namespace.
    Args:
        id: The environment id to parse
    Returns:
        A tuple of environment namespace, environment name and version number
    Raises:
        Error: If the environment id does not a valid environment regex
    """
    match = ENV_ID_RE.fullmatch(id)
    if not match:
        raise error.Error(
            f"Malformed environment ID: {id}."
            f"(Currently all IDs must be of the form [namespace/](env-name)-v(version). (namespace is optional))"
        )
    namespace, name, version = match.group("namespace", "name", "version")
    if version is not None:
        version = int(version)

    return namespace, name, version


def get_env_id(ns: Optional[str], name: str, version: Optional[int]) -> str:
    """Get the full env ID given a name and (optional) version and namespace. Inverse of :meth:`parse_env_id`.
    Args:
        ns: The environment namespace
        name: The environment name
        version: The environment version
    Returns:
        The environment id
    """

    full_name = name
    if version is not None:
        full_name += f"-v{version}"
    if ns is not None:
        full_name = ns + "/" + full_name
    return full_name


@dataclass
class EnvSpec:
    """A specification for creating environments with `mlopskit.make`.
    * id: The string used to create the environment with `mlopskit.make`
    * entry_point: The location of the environment to create from
    * reward_threshold: The reward threshold for completing the environment.
    * nondeterministic: If the observation of an environment cannot be repeated with the same initial state, random number generator state and actions.
    * max_episode_steps: The max number of steps that the environment can take before truncation
    * order_enforce: If to enforce the order of `reset` before `step` and `render` functions
    * autoreset: If to automatically reset the environment on episode end
    * disable_env_checker: If to disable the environment checker wrapper in `mlopskit.make`, by default False (runs the environment checker)
    * kwargs: Additional keyword arguments passed to the environments through `mlopskit.make`
    """

    id: str

    # Environment arguments
    kwargs: dict = field(default_factory=dict)

    # post-init attributes
    namespace: Optional[str] = field(init=False)
    name: str = field(init=False)
    version: Optional[int] = field(init=False)

    def __post_init__(self):
        # Initialize namespace, name, version
        self.namespace, self.name, self.version = parse_env_id(self.id)

    def make(self, **kwargs) -> HTTPClient:
        # For compatibility purposes
        self.client = HTTPClient(**kwargs)
        return make(self, **kwargs)


# return_type = ["dbobj", "dblink"]
def make(
    id: Union[str, EnvSpec] = None,
    help: bool = False,
    autoreset: bool = False,
    disable_env_checker: Optional[bool] = None,
    **kwargs,
):
    if id is None:
        msg = (
            f'The correct naming convention is "$ops_type/$model_name-v$version".'
            f'Valid ops_type options are: ["model", "cache", "db", "config", "meta", "mlproject"].'
            f"If v$version is empty, further instructions will be provided. "
            f"Alternatively, inputting `client` will return the original client."
        )
        logger.warning(colorize(msg, "yellow", True, False))
        return
    if isinstance(id, EnvSpec):
        spec_ = id
    else:
        module, id = (None, id) if ":" not in id else id.split(":")
        if module is not None:
            try:
                importlib.import_module(module)
            except ModuleNotFoundError as e:
                raise ModuleNotFoundError(
                    f"{e}. Environment registration via importing a module failed. "
                    f"Check whether '{module}' contains env registration and can be imported."
                )
        spec_ = id
        _kwargs = kwargs.copy()
        host = _kwargs.get("host")
        config = _kwargs.get("config")

        client = HTTPClient(host=host, config_file=config)
        if id.startswith("client") and id.endswith("client"):
            p = {"host": "set/get, default:get", "config": "config file, default:None"}
            logger.info(
                "Usage of mlopskit-client",
                Params=colorize(p, "cyan", True, False),
                Return="HTTPClient",
            )
            msg = "Return of mlopskit-client: HTTPClient"
            if help:
                return
            return HTTPClient(host=host, config_file=config)
        ns, name, version = parse_env_id(id)
        if not ns:
            msg = (
                f'The correct naming convention is "$ops_type/$model_name-v$version".'
                f'Valid ops_type options are: ["model", "cache", "db", "config", "meta", "mlproject"].'
                f"If v$version is empty, further instructions will be provided. "
                f"Alternatively, inputting `client` will return the original client."
            )
            logger.warning(colorize(msg, "yellow", True, False))
            return
        if version:
            version = str(version)
        logger.info(
            "APIs of mlopskit", ops_type=ns, model_name=name, model_version=version
        )
        if ns in ["db", "cache", "model"]:
            try:
                model = client.mlflow_client.get_model(name)
            except:
                if ns in ["db", "cache"]:
                    msg = f"Model {name} is not exist,To resolve this issue, you will need to create and register the {name} model using `push` method before create db/cache"
                    logger.error(colorize(msg, "red", True, False))
                    return
                else:
                    msg = f"->Model {name} is not exist,we will create and register it"
                    logger.warning(colorize(msg, "yellow", True, False))

            try:
                versions = [
                    int(v.version)
                    for v in client.mlflow_client.list_model_all_versions(name)
                ]
                latest_version = max(versions)
                color_versions = colorize(versions, "green", True, True)
                logger.info(
                    f"The list of all versions for the current model is {color_versions}."
                )
                if (
                    version is not None
                    and latest_version is not None
                    and latest_version > int(version)
                ):
                    logger.warning(
                        f"The version {version} is out of date. You should consider "
                        f"upgrading to version `v{latest_version}`."
                    )

                if version is None and latest_version is not None:
                    if ns in ["db", "cache"]:
                        logger.error(
                            colorize(
                                f"you will have to create or specify a Version of  Model {name} first",
                                "red",
                                True,
                                False,
                            )
                        )
                        return
                    if ns == "model":
                        logger.warning(
                            colorize(
                                (
                                    f"Using the latest versioned model `{latest_version}` "
                                    f"instead of the unversioned model `{version}`."
                                    f"If you insist on doing so, we will create a new version `{latest_version+1}` for you."
                                ),
                                "yellow",
                                True,
                                False,
                            )
                        )
                if version is not None and int(version) not in versions:
                    msg = (
                        f"Version {version} not found in model {name}, you can chose a verion"
                        f"that <= {latest_version} or create a new version {latest_version+1} "
                        f"by remove `v{version}` in the input param"
                    )
                    logger.warning(colorize(msg, "yellow", True, False))
                    return
            except:
                if ns in ["db", "cache"]:
                    msg = f"you will have to create or specify a Version of  Model {name} first"
                    logger.error(colorize(msg, "red", True, True))
                    return
                else:
                    msg = f"we will create a first verison of model {name}"
                    logger.warning(colorize(msg, "yellow", True, True))

        valid_ops = ["model", "cache", "db", "config", "meta", "mlproject"]
        assert ns in valid_ops, f"命名空间: {ns} 斜杠前的部分有效内容为 {valid_ops}"

        if ns == "mlproject":
            if version is not None:
                _default_project_name = f"{name}-v{version}"
            else:
                _default_project_name = f"{name}"
            p = {
                "project_name": f"str, default:`{_default_project_name}`",
                "project_path": "default: `os.getcwd`",
                "remote": "default:False",
                "version": f"the created local project will upload to `{name}-v$version`",
            }
            logger.info(
                "Usage of mlopskit-mlproject",
                Params=colorize(p, "cyan", True, False),
            )
            if help:
                return

            project_name = _kwargs.get("project_name", _default_project_name)
            project_path = _kwargs.get("project_path", os.getcwd())
            remote = _kwargs.get("remote", False)
            s_version = _kwargs.get("version", False)
            if remote:
                logger.info(
                    f"We will create an ML project in the directory specified by you locally, "
                    f"and also create the corresponding version directory in the remote model for it.",
                    Params=colorize(p, "cyan", True, False),
                )

            project_dir = os.path.join(project_path, project_name)
            if os.path.exists(project_dir):
                msg = f"Directory {project_dir} exists"
                logger.error(colorize(msg, "red", True, False))
                return
            else:
                os.makedirs(project_dir)
                msg = f"Directory {project_dir} created successfully"
                logger.info(colorize(msg, "green", True, False))

                create_structure(project_dir, project_name, name, version)

                msg = f"ML Project {project_name} is created!"
                logger.info(colorize(msg, "green", True, False))
                if remote:
                    if s_version:
                        remote_model_id = get_env_id("model", name, s_version)
                    else:
                        remote_model_id = get_env_id("model", name, version)
                    # print(project_dir,"project_dir")

                    logger.info(
                        f"Next, we will upload the newly created ML "
                        f"project {project_name} to the remote model space {remote_model_id}..."
                    )
                    make(remote_model_id, to_push_file=project_name)

                return

        if ns == "meta":
            p = {"meta_ops": "get/set, default:get", "set": {"meta_content": "Dict"}}
            logger.info(
                "Usage of mlopskit-meta",
                Params=colorize(p, "cyan", True, False),
            )

            if help:
                return
            meta_ops = _kwargs.get("meta_ops", "get")
            if meta_ops == "get":
                meta_seted = client.get_model_meta(name)
                if meta_seted:
                    return meta_seted
                else:
                    return {}

            elif meta_ops == "set":
                meta_content = _kwargs.get("meta_content")

                if not meta_content:
                    msg = (
                        f"Please ensure that the parameter `meta_content` is not empty."
                    )
                    logger.error(colorize(msg, "red", True, False))
                    return
                if version:
                    meta_content["version"] = str(version)
                beijing_tz = pytz.timezone("Asia/Shanghai")
                beijing_time = datetime.datetime.now(beijing_tz)
                meta_content["updated_at"] = str(beijing_time)
                client.update_model_meta(name, **meta_content)
                msg = f"meta data of model {name} is updated to Version {version}"
                logger.info(colorize(msg, "green", True, False))
                return
            else:
                msg = f"The feature is currently not available at the moment."
                logger.error(colorize(msg, "red", True, False))
                return

        if ns == "config":
            p = {
                "config_ops": "set/get, default:get",
                "get": {
                    "config_path": "default:None",
                    "set": {
                        "config_content": "config cintent,Dict",
                        "config_path": "default:None",
                    },
                },
            }

            logger.info(
                "Usage of mlopskit-config",
                Params=colorize(p, "cyan", True, False),
            )
            if help:
                return
            config_ops = _kwargs.get("config_ops", "get")
            if config_ops == "get":
                config_path = _kwargs.get("config_path")
                config_info = client.get_config(config_path=config_path)
                return config_info

            elif config_ops == "set":
                config_path = _kwargs.get("config_path")
                config_content = _kwargs.get("config_content", {})
                client.set_config(config_content, config_path=config_path)
            else:
                print(colorize("暂不支持", "red", False, True))
                return

        if ns == "db":
            p = {"db_type": "sqlite/postgres/tiny, default:sqlite"}
            logger.info(
                "Usage of mlopskit-db",
                Params=colorize(p, "cyan", True, False),
            )
            if help:
                return
            db_type = _kwargs.get("db_type", "sqlite")
            db = client.build_data_store(name, version, db_type=db_type)
            return db

        if ns == "cache":
            p = {
                "db_type": "rlite/redis/sfdb/diskcache, default:rlite",
                "return_type": "dblink/dbobj, default: dbobj",
                "db_name": "default: rlite_model.cache",
            }
            logger.info(
                "Usage of mlopskit-cache",
                Params=colorize(p, "cyan", True, False),
            )
            if help:
                return
            db_name = _kwargs.get("db_name", "rlite_model.cache")
            db_type = _kwargs.get("db_type", "rlite")
            return_type = _kwargs.get("return_type", "dbobj")
            db = client.build_cache_store(
                name,
                version,
                db_name=db_name,
                db_type=db_type,
                return_type=return_type,
            )
            return db

        if ns == "model":
            p = {
                "ops_type": "push/pull/serving/predict/killservice/serving_status, default:push"
            }
            logger.info(
                "Usage of mlopskit-model",
                Params=colorize(p, "cyan", True, False),
            )

            msg_push = {
                "to_push_file": "model file/dir to upload to remote model space",
                "push_type": "file/pickle, default: file",
            }
            logger.info(
                "Usage of mlopskit-push",
                Params=colorize(msg_push, "cyan", True, False),
            )

            p_pull = {"save_path": "local path to download model"}
            logger.info(
                "Usage of mlopskit-pull",
                Params=colorize(p_pull, "cyan", True, False),
            )

            if help:
                return
            ops_type = _kwargs.get("ops_type", "push")
            valid_ops_type = [
                "push",
                "pull",
                "serving",
                "predict",
                "killservice",
                "serving_status",
            ]
            assert (
                ops_type in valid_ops_type
            ), f"模型操作类型为: {ns} 时，有效的操作方式为 {valid_ops_type}"
            if ops_type == "push":

                to_push_file = _kwargs.get("to_push_file")
                if to_push_file is None:
                    logger.error(
                        colorize(
                            f"You need to specify the parameter `to_push_file`.",
                            "red",
                            True,
                            False,
                        )
                    )
                    return
                push_type = _kwargs.get("push_type", "file")
                run_id = _kwargs.get("run_id")
                tags = _kwargs.get("tags")
                r = client.push(
                    name,
                    version,
                    to_push_file=to_push_file,
                    run_id=run_id,
                    tags=tags,
                )
                ops_result = r
                msg = ops_result["details"]
                if ops_result["status"] == "ok":
                    # print(colorize(msg, "green", False, True))
                    logger.info(colorize(msg, "green", True, True))
                else:
                    logger.error(
                        "there is some errors when model ops",
                        msg=colorize(msg, "red", True, True),
                    )

            if ops_type == "pull":
                save_path = _kwargs.get("save_path", os.getcwd())
                client.pull(name, version, save_path=save_path)
                msg = f"model:{name}-V{version} is download at {save_path}"
                # print(colorize(msg, "green", False, True))
                logger.info(colorize(msg, "green", True, True))
                return True
