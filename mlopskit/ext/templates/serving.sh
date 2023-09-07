export MLOPSKIT_DEFAULT_PACKAGE={{server_name}}
gunicorn \
    --workers {{workers}} \
    -b :{{port}} \
    --preload \
    --worker-class=uvicorn.workers.UvicornWorker \
    'mlopskit.api:create_mlopskit_app()'
