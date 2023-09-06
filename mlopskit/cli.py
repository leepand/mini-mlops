import os
import sys
import time

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
from mlopskit.ext.prompts.prompt import create_template, readfile
from mlopskit.utils.file_utils import data_dir
from mlopskit.utils.shell_utils import get_port_status, start_service
from mlopskit.utils.killport import kill9_byport
from mlopskit.ext.store.yaml.yaml_data import YAMLDataSet
from mlopskit.config import SERVER_PORT_CONFIG, DEFAULT_SERVER_CONFIG

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
    sh.mkdir(project_path)
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
def run(service):
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
    mlopskit_config_json = YAMLDataSet(mlopskit_config).load()
    mlflow_url = mlopskit_config_json.get("mlflow_url")
    mlflow_port = mlflow_url.split(":")[-1]
    mlflow_port_status = get_port_status(mlflow_port)
    # logger.info(f"mlflow_port_status: {mlflow_port_status}!", port=mlflow_port_status)

    # start mlflow service
    if service in ["mlflow", "all"]:
        if mlflow_port_status == "running":
            c = input(f"Confirm kill the mlflow port {mlflow_port} (y/n)")
            if c == "n":
                return None
            else:
                kill9_byport(mlflow_port)
                time.sleep(1)
                logger.warning(f"port {mlflow_port} is killed!", name="mlflow service")

        sh.mkdir(mlflow_workspace)
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