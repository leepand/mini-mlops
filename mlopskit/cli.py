import os
import sys

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
from mlopskit.ext.prompts.prompt import PromptTemplate, create_template, readfile
from mlopskit.utils.file_utils import make_containing_dirs

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
        sh.write(reward_file_path, rewardserver_contents)
        sh.write(utils_file_path, readfile(sh, "utils.py"))

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
