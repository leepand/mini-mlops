from pathlib import Path, PurePosixPath
import os
import sys
import time
from datetime import datetime

import click
import git

# import rich_click as click

import humanize
from rich.console import Console
from rich.markup import escape
from rich.progress import Progress, track
from rich.table import Table
from rich.tree import Tree

from mlopskit.assets.cli import assets_cli
import mlopskit.ext.shellkit as sh
from mlopskit.ext.prompts.prompt import create_template, readfile, PromptTemplate
from mlopskit.utils.file_utils import data_dir, get_first_level_directories
from mlopskit.utils.shell_utils import get_port_status, start_service
from mlopskit.utils.killport import kill9_byport
from mlopskit.ext.store.yaml.yaml_data import YAMLDataSet
from mlopskit.pipe import ConfigManager, Pipe
from mlopskit.config import (
    SERVER_PORT_CONFIG,
    DEFAULT_SERVER_CONFIG,
    FRONTEND_PATH,
    SERVER_PATH,
)
from mlopskit.pastry.api import make

from .ext.gitkit.create import (
    repo_create,
    repo_find,
    tree_from_index,
    commit_create,
    object_find,
)
from .ext.gitkit.add import add as repo_add
from .ext.gitkit.index import index_read
from .ext.gitkit.config import gitconfig_user_get, gitconfig_read
from .ext.gitkit.branch import branch_get_active
from .ext.gitkit.file import repo_file
from .ext.gitkit.gitRepository import cmd_status_head_index

from structlog import get_logger

logger = get_logger(__name__)


@click.group()
def mlopskit_cli():
    sys.path.append(os.getcwd())
    pass


mlopskit_cli.add_command(assets_cli)


@mlopskit_cli.command("init", no_args_is_help=True)
@click.option(
    "--project",
    "-p",
    help="project name",
    type=str,
    default="my_project",
    show_default=True,
)
@click.option(
    "--model",
    "-m",
    help="model name",
    type=str,
    default="my_model",
    show_default=True,
)
@click.option(
    "--version",
    "-v",
    help="model version",
    type=str,
    default="1",
    show_default=True,
)
def init(project, model, version):
    """
    Init ML project from ml_template.
    """
    base_path = os.getcwd()
    project_path = os.path.join(base_path, project)
    # make_containing_dirs(project_path)
    # sh.mkdir(project_path)
    repo_create(project_path)
    sh.mkdir(f"{project_path}/src")
    sh.mkdir(f"{project_path}/config")
    sh.mkdir(f"{project_path}/notebooks")
    sh.mkdir(f"{project_path}/logs")
    with sh.cd(project_path):
        # 读取包中的文件内容-readme.md
        readme_contents = create_template(
            filename="README.md",
            input_variables=["model_name"],
            template_format="f-string",
            model_name=model,
        )

        readme_path = os.path.join(project_path, "README.md")
        sh.write(readme_path, readme_contents)

        recomserver_contents = create_template(
            filename="recomserver.py",
            input_variables=["model_name", "version"],
            template_format="jinja2",
            model_name=model,
            version=version,
        )

        # read recomserver.py
        recom_file_path = os.path.join(project_path, "src/recomserver.py")
        sh.write(recom_file_path, recomserver_contents)

        # read rewardserver.py
        rewardserver_contents = create_template(
            filename="rewardserver.py",
            input_variables=["model_name", "version"],
            template_format="jinja2",
            model_name=model,
            version=version,
        )

        # read recomserver.py
        reward_file_path = os.path.join(project_path, "src/rewardserver.py")
        utils_file_path = os.path.join(project_path, "src/utils.py")
        config_dev_meta_path = os.path.join(project_path, "config/server_dev.yml")
        config_prod_meta_path = os.path.join(project_path, "config/server_prod.yml")
        sh.write(reward_file_path, rewardserver_contents)
        sh.write(utils_file_path, readfile(sh, "utils.py"))
        c = YAMLDataSet(config_dev_meta_path)
        c.save(SERVER_PORT_CONFIG)
        c_p = YAMLDataSet(config_prod_meta_path)
        c_p.save(SERVER_PORT_CONFIG)

        # read config.py
        config_contents = create_template(
            filename="config.py",
            input_variables=["model_name"],
            template_format="jinja2",
            model_name=model,
        )
        config_notebooks_path = os.path.join(project_path, "notebooks/config.py")
        sh.write(config_notebooks_path, config_contents)

        # read open_debug_db.py
        open_debug_db_contents = create_template(
            filename="open_debug_db.py",
            input_variables=["model_name"],
            template_format="jinja2",
            model_name=model,
        )
        open_debug_db_path = os.path.join(project_path, "notebooks/open_debug_db.py")
        sh.write(open_debug_db_path, open_debug_db_contents)

        # read serving.py
        serving_contents = create_template(
            filename="serving.py",
            input_variables=["model_name"],
            template_format="jinja2",
            model_name=model,
        )
        serving_path = os.path.join(project_path, "notebooks/serving.py")
        sh.write(serving_path, serving_contents)
        logs_path = os.path.join(project_path, "logs/README.md")
        sh.write(logs_path, "## serving logs\n")

    logger.info(f"Project {project} is created!", name=project)


@mlopskit_cli.command("init_fromgit", no_args_is_help=True)
@click.option(
    "--project",
    "-p",
    help="project name",
    type=str,
    default="my_project",
    show_default=True,
)
def init_fromgit(project):
    """
    Init ML project from github repo ml_template.
    """
    repo = git.Repo.init(path=".")
    new_repo = git.Repo.clone_from(
        url="https://github.com/leepand/ml_template", to_path=project
    )
    # print(f"Project {project} is created!")
    logger.info(f"Project {project} is created!", name=project)


@mlopskit_cli.command("run", no_args_is_help=True)
@click.option(
    "--service",
    "-s",
    help="service name",
    type=str,
    default="all",
    show_default=True,
)
@click.option(
    "--build",
    "-b",
    help="build main ui service",
    type=str,
    default="false",
    show_default=True,
)
@click.option(
    "--host",
    "-h",
    help="host of  main ui service",
    type=str,
    default="0.0.0.0",
    show_default=True,
)
@click.option(
    "--port",
    "-p",
    help="port of  main ui service",
    type=str,
    default="8080",
    show_default=True,
)
@click.option(
    "--backend",
    help="run backend of  main ui service",
    type=str,
    default="false",
    show_default=True,
)
def run(service, build, host, port, backend):
    """
    start services: main/mlflow/model server.
    """
    base_path = data_dir()
    mlopskit_config = os.path.join(base_path, "mlops_config.yml")
    if os.path.exists(mlopskit_config):
        logger.info(f"mlopskit config file mlops_config.yml!", path=mlopskit_config)
    else:
        logger.info(
            f"mlopskit config file mlops_config.yml is not exists!",
            path=mlopskit_config,
        )
        YAMLDataSet(mlopskit_config).save(DEFAULT_SERVER_CONFIG)

        logger.info(
            f"we use default config info and create file mlops_config.yml!",
            mlopskit_config=DEFAULT_SERVER_CONFIG,
        )

    mlflow_workspace = os.path.join(base_path, "mlflow_workspace")
    sh.mkdir(mlflow_workspace)
    mlopskit_config_json = YAMLDataSet(mlopskit_config).load()
    mlflow_url = mlopskit_config_json.get("mlflow_url")
    model_server_url = mlopskit_config_json.get("model_url")
    model_server_port = model_server_url.split(":")[-1]
    mlflow_port = mlflow_url.split(":")[-1]
    # logger.info(f"mlflow_port_status: {mlflow_port_status}!", port=mlflow_port_status)

    # start mlflow service
    if service in ["mlflow", "all"]:
        mlflow_port_status = get_port_status(mlflow_port)
        if mlflow_port_status == "running":
            c = input(f"Confirm kill the mlflow port {mlflow_port} (y/n)")
            if c == "n":
                return None
            else:
                kill9_byport(mlflow_port)
                time.sleep(1)
                logger.warning(f"port {mlflow_port} is killed!", name="mlflow service")

        with sh.cd(mlflow_workspace):
            sh.write(
                "run.sh",
                f"""nohup mlflow server  \
                    --default-artifact-root artifacts \
                        --backend-store-uri sqlite:///mlflow.db \
                            --host 0.0.0.0 \
                                  -p {mlflow_port} >run_mlflow.log 2>&1 &""",
            )
            mlflow_run_msg = start_service("sh run.sh")

            logger.info(
                f"stdout info: {mlflow_run_msg}!",
                name="mlflow service serving",
            )
    # start model server
    if service in ["model_server", "all"]:
        model_server_port_status = get_port_status(model_server_port)
        if model_server_port_status == "running":
            c = input(f"Confirm kill the model server port {model_server_port} (y/n)")
            if c == "n":
                return None
            else:
                kill9_byport(model_server_port)
                time.sleep(1)
                logger.warning(
                    f"port {model_server_port} is killed!", name="model server service"
                )
        with sh.cd(mlflow_workspace):
            sh.write(
                os.path.join(mlflow_workspace, "model_server.py"),
                "from mlopskit.pastry.dam import Dam\ndam = Dam()\n",
            )

            # 5005 与HTTPClient().get_config() 中的model_url的ip和port一致
            sh.write(
                os.path.join(mlflow_workspace, "run_model_server.sh"),
                f"uvicorn model_server:dam.http_server --host 0.0.0.0 --port {model_server_port}",
            )

            model_server_run_msg = start_service(
                "nohup sh run_model_server.sh > run_model_server.log 2>&1 &"
            )

            logger.info(
                f"stdout info: {model_server_run_msg}!",
                name="model server service serving",
            )
    if service in ["main", "all"]:
        # start main serivce UI
        if build == "true":
            print("####### BUILDING FRONTEND #######")
            with sh.cd(FRONTEND_PATH):
                # read API.js
                js_file_path = os.path.join(FRONTEND_PATH, "src/api/api.js")
                api_file_template = PromptTemplate.from_file(
                    js_file_path,
                    input_variables=["host", "port"],
                    template_format="jinja2",
                )
                api_js_contents = api_file_template.format(host=host, port=port)
                sh.write(js_file_path, api_js_contents)

                build_msg = start_service("npm install && npm run build", timeout=3600)
                logger.info(
                    f"build ui info: {build_msg}!",
                    name="main service build",
                )
                index_file_src = os.path.join(FRONTEND_PATH, "dist/index.html")
                index_file_dst = os.path.join(SERVER_PATH, "templates/index.html")
                main_files_src = os.path.join(FRONTEND_PATH, "dist")
                main_files_dst = os.path.join(SERVER_PATH, "static")
                sh.cp(src=index_file_src, dst=index_file_dst)
                sh.cp(src=main_files_src, dst=main_files_dst)

            return "build done!"

        main_server_port_status = get_port_status(port)
        if main_server_port_status == "running":
            c = input(f"Confirm kill the model server port {port} (y/n)")
            if c == "n":
                return None
            else:
                kill9_byport(port)
                time.sleep(1)
                logger.warning(f"port {port} is killed!", name="model server service")

        if backend == "true":
            _server_host = "0.0.0.0"
            with sh.cd(mlflow_workspace):
                main_service_msg = start_service(
                    script=f"nohup gunicorn --workers=3 -b {_server_host}:{port}  mlopskit.server.wsgi:app >main_server.log 2>&1 &"
                )
                logger.info(
                    f"serving ui info: {main_service_msg}!",
                    name="main service serving",
                )
        else:
            _server_host = "0.0.0.0"
            path = os.path.realpath(os.path.dirname(__file__))
            with sh.cd(path):
                main_service_msg = start_service(
                    script=f"gunicorn --workers=3 -b {_server_host}:{port}  server.wsgi:app >>web-predict.log;"
                )
                logger.info(
                    f"serving ui info: {main_service_msg}!",
                    name="main service serving",
                )


@mlopskit_cli.command("regmodel", no_args_is_help=True)
@click.option("--name", help="model name", required=True)
@click.option(
    "--filesdir",
    help="model files dir name",
    is_flag=False,
    required=True,
    show_default=True,
)
@click.option(
    "--confirm", help="confirm", is_flag=True, default=True, show_default=True
)
def regmodel(name, filesdir, confirm):
    """
    Register a trained machine learning model to the model repository/registry for discovery and deployment.
    """
    model_name = name
    try:
        if confirm:
            c = input(
                "Confirm register model {} files to {} (y/n)".format(
                    model_name, "remote repository"
                )
            )
            if c == "n":
                return None
        else:
            c = "y"
        if c == "y":
            if not filesdir:
                logger.warning(f"you have to specify `filesdir`")
                return

            make(f"model/{model_name}", to_push_file=filesdir)
    except Exception as e:
        click.echo(e)


@mlopskit_cli.command("pull", no_args_is_help=True)
@click.option("--pipe", help="Pipe name", required=True)
@click.option(
    "--profile", help="env name", required=True, default="dev", show_default=True
)
@click.option("--version", help="version", is_flag=False, show_default=True)
@click.option(
    "--preview", help="Preview", is_flag=True, default=True, show_default=True
)
def pull(pipe, version, profile, preview):
    """
    Pull model and code from remote repo.
    """
    pipe_name = pipe
    try:
        pipe = Pipe(pipe_name, profile=profile)
        if preview:
            result = pipe.pull(dryrun=True, version=version)
            logger.info(f"Pull codes:{result}")
        else:
            result = pipe.pull(dryrun=False, version=version)
            logger.info(f"Pull codes:{result}")
    except Exception as e:
        click.echo(e)


@mlopskit_cli.command("push", no_args_is_help=True)
@click.option("--pipe", help="Pipe name", required=True)
@click.option(
    "--profile", help="env name", required=True, default="dev", show_default=True
)
@click.option("--filename", help="file/dir name to push", required=True)
@click.option("--version", help="version", is_flag=False, show_default=True)
@click.option(
    "--exclude", help="exclude", is_flag=False, default="*.txt", show_default=True
)
@click.option(
    "--toremote", help="to_remote", is_flag=True, default=False, show_default=True
)
@click.option(
    "--preview", help="Preview", is_flag=True, default=True, show_default=True
)
def push(pipe, filename, version, exclude, toremote, profile, preview):
    """
    Push model and code from local repo to remote repo.
    """
    pipe_name = pipe
    try:
        pipe = Pipe(pipe_name, profile=profile)
        if preview:
            result = pipe.push(
                dryrun=True,
                filename=filename,
                version=version,
                exclude=exclude,
                to_remote=toremote,
            )
            logger.info(f"Push codes:{result}")
        else:
            result = pipe.push(
                dryrun=False,
                filename=filename,
                version=version,
                exclude=exclude,
                to_remote=toremote,
            )
            logger.info(f"Push codes:{result}")
    except Exception as e:
        click.echo(e)


@mlopskit_cli.command("scan_remote", no_args_is_help=True)
@click.option(
    "--pipe", help="pipe name", required=True, default="all", show_default=True
)
@click.option(
    "--profile", help="env name", required=True, default="dev", show_default=True
)
@click.option("--version", help="verson ex.v1", required=False, show_default=True)
@click.option(
    "--filecfg",
    help="filecfg name",
    required=False,
    default="~/mlopskit/cfg.json",
    show_default=True,
)
def scan_remote(pipe, filecfg, version, profile):
    """
    Scan remote files of diff model's envs and versions.
    """
    try:
        if profile not in ["dev", "prod", "preprod"]:
            profile = "default"
        configmgr = ConfigManager(filecfg=filecfg, profile=profile)
        config = configmgr.load()
        cfg_profile = config
        filerepo = cfg_profile["filerepo"]
        if pipe == "all":
            dirpath = Path(filerepo)
            files = get_first_level_directories(dirpath)
            logger.info(f"models remote info:{files}")
            return
        else:
            if version:
                dirpath = Path(os.path.join(filerepo, pipe, version))
            else:
                dirpath = Path(os.path.join(filerepo, pipe))
                files = get_first_level_directories(dirpath)
                logger.info(f"models remote info:{files}")
                return
        _dir = str(dirpath) + os.sep
        files = [
            str(PurePosixPath(p.relative_to(_dir)))
            for p in dirpath.glob("**/*")
            if not p.is_dir()
        ]

        logger.info(f"models remote info:{files}")
    except Exception as e:
        click.echo(e)


@mlopskit_cli.command("remove", no_args_is_help=True)
@click.option("--pipe", help="Pipe name", required=True)
@click.option(
    "--profile", help="env name", required=True, default="dev", show_default=True
)
@click.option("--version", help="version", is_flag=False, show_default=True)
@click.option(
    "--confirm", help="confirm", is_flag=True, default=True, show_default=True
)
@click.option("--files", help="files", is_flag=False, default="all", show_default=True)
def remove(pipe, version, confirm, profile, files):
    """
    Remove files of remote (version).
    """
    pipe_name = pipe
    try:
        pipe = Pipe(pipe_name, profile=profile)
        files = pipe.delete_files_remote(version=version, files=files, confirm=confirm)
        logger.info(f"delete remote repo files:{files}")
    except Exception as e:
        click.echo(e)


@mlopskit_cli.command("killport", no_args_is_help=True)
@click.option("--port", help="model port", required=True)
@click.option(
    "--confirm", help="confirm", is_flag=True, default=True, show_default=True
)
def killport(port, confirm):
    """
    Kill port process.
    """
    try:
        if confirm:
            c = input("Confirm port {} to {} (y/n)".format(port, "kill"))
            if c == "n":
                return None
        else:
            c = "y"
        if c == "y":
            kill9_byport(port)
    except Exception as e:
        click.echo(e)


@mlopskit_cli.command("add", no_args_is_help=True)
@click.option("--path", help="model path", default=".", required=False)
def cmd_add(path):
    """
    Add files contents to the index.
    """
    try:
        repo = repo_find()
        # paths = list(sh.walkfiles())
        if os.path.isdir(path):
            paths_all = list(sh.walk(path, exclude=".git"))
            files = [file for file in paths_all if os.path.isfile(file)]
        else:
            files = [path]
        repo_add(repo, files)
    except Exception as e:
        click.echo(e)


@mlopskit_cli.command("commit", no_args_is_help=True)
@click.option("--msg", "-m", help="commit message", default="update", required=True)
def cmd_commit(msg):
    """
    Message to associate with this commit.
    """
    try:
        repo = repo_find()
        index = index_read(repo)
        # Create trees, grab back SHA for the root tree.
        tree = tree_from_index(repo, index)
        # Create the commit object itself
        commit = commit_create(
            repo,
            tree,
            object_find(repo, "HEAD"),
            gitconfig_user_get(gitconfig_read()),
            datetime.now(),
            msg,
        )

        # Update HEAD so our commit is now the tip of the active branch.
        active_branch = branch_get_active(repo)
        print(f"[{active_branch}] {msg}")
        print(f"Committer: {commit}")
        cmd_status_head_index(repo=repo, index=index)
        if active_branch:  # If we're on a branch, we update refs/heads/BRANCH
            with open(
                repo_file(repo, os.path.join("refs/heads", active_branch)), "w"
            ) as fd:
                fd.write(commit + "\n")
        else:  # Otherwise, we update HEAD itself.
            with open(repo_file(repo, "HEAD"), "w") as fd:
                fd.write("\n")
    except Exception as e:
        click.echo(e)
