release: flask db upgrade
web: gunicorn avwx_account.__init__:app -c gunicorn_config.py --log-file -