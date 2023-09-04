MODEL_SERVER_MAKEFILE_CPU = """\
hostmodel:
	cd {model_path} && python3 -m venv venv && source venv/bin/activate && \
    {command}
"""  # noqa: E501


MODEL_SERVER_MAKEFILE_CPU_REQUI = """\
hostmodel:
	cd {model_path} && \
    pip install -r requirements.txt && \
    {command}
"""  # noqa: E501
