import os
import stat

from mlopskit.pastry.api.colorize import colorize
from mlopskit.utils.shell_utils import (
    get_port_status,
    wait_until_port_used,
    start_service,
)
from mlopskit.ext.prompts.prompt import create_template
import mlopskit.ext.shellkit as sh
from mlopskit.utils.killport import kill9_byport

from jinja2 import Environment, FileSystemLoader

from structlog import get_logger

logger = get_logger(__name__)


def _generate_serverfile(save_dir, server_name, port, workers=4, suffix="sh"):
    # gen serve template
    serve_file_name = "ServerFile.j2"
    serve_file_contents = create_template(
        filename=serve_file_name,
        input_variables=["workers", "server_name", "port"],
        template_format="jinja2",
        workers=workers,
        server_name=server_name,
        port=port,
    )
    saved_file = os.path.join(save_dir, f"{server_name}_{port}.{suffix}")
    local_server_file = f"{server_name}_{port}.{suffix}"
    local_server_file_name = f"{server_name}_{port}"
    run_cmd_file = os.path.join(save_dir, f"run_{server_name}_{port}.sh")

    logger.debug("Generating Model Serverfile via templates from ServerFile.j2 ...")
    sh.write(saved_file, serve_file_contents)

    parent_directory = os.path.dirname(save_dir)
    log_directory = os.path.join(parent_directory, "logs")
    os.makedirs(log_directory, exist_ok=True)  # create dir if doesn't exist

    if suffix == "sh":
        run_cmd_contents = f"nohup sh {local_server_file} > ../logs/{local_server_file_name}.log 2>&1 &"
    elif suffix == "py":
        run_cmd_contents = f"nohup python {local_server_file} > ../logs/{local_server_file_name}.log 2>&1 &"
    else:
        logger.debug(
            "Currently, only service files of sh and py types are supported for execution."
        )
        return

    logger.debug("Generating run cmd script ...")
    sh.write(run_cmd_file, run_cmd_contents)

    if suffix == "sh":
        st = os.stat(saved_file)
        os.chmod(saved_file, st.st_mode | stat.S_IEXEC)

    st2 = os.stat(run_cmd_file)
    os.chmod(run_cmd_file, st2.st_mode | stat.S_IEXEC)


def prebuild_server(
    prebuild_path,
    server_name,
    ports=[],
    workers=4,
    suffix="sh",
    serving=False,
    model_name=None,
    server_type="recom",
):
    if not isinstance(ports, list):
        logger.error(
            "Failed to build service %s: %s",
            server_name,
            "the ports type is list,e.g. [5001,5002]",
        )
        return
    for port in ports:
        _generate_serverfile(
            save_dir=prebuild_path,
            server_name=server_name,
            port=port,
            workers=workers,
            suffix=suffix,
        )

    if serving:
        try:
            msgs = []
            for _port in ports:
                port_status = get_port_status(_port)
                if port_status == "running":
                    kill9_byport(_port)

                run_cmd_file = os.path.join(
                    prebuild_path, f"run_{server_name}_{_port}.sh"
                )
                _script = f"cd {prebuild_path} && sh {run_cmd_file}"
                msg = start_service(script=_script)
                msgs.append(f"{msg},and port is {_port}")
                # time.sleep(2)
                port_status2 = wait_until_port_used(_port)
                # port_status2 = get_port_status(_port)
                if port_status2:
                    logger.info(
                        colorize(
                            f"model: {model_name}, server:{server_name} port: {_port} is running",
                            "green",
                            True,
                            True,
                        )
                    )
                else:
                    logger.warning(
                        colorize(
                            f"model service: {model_name},server:{server_name} port: {_port} is failed",
                            "red",
                            True,
                            False,
                        )
                    )

            return msgs

        except Exception as e:
            logger.error("Failed to build service %s: %s", server_name, e)
            return
