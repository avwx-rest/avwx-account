# AVWX-Account

[![Requirements Status](https://requires.io/github/flyinactor91/AVWX-Account/requirements.svg?branch=master)](https://requires.io/github/flyinactor91/AVWX-Account/requirements/?branch=master)

Account management app for AVWX-API

## Setup

First we should install the app requirements and copy the env file. I recommend always installing into a virtual environment.

```bash
pip install -r requirements.txt
cp .env.sample .env
```

The app uses a Postgres backend. To run locally, you'll need to create a rocky database and owner.

```sql
CREATE USER avwx;
CREATE DATABASE avwx_account OWNER avwx;
```

Before we can run the migrations, we need to tell Flask where the app is.

```bash
export FLASK_APP=avwx_account/__init__.py
export FLASK_ENV=development
```

Now we can populate the database.

```bash
flask db upgrade
```

Now you should be able to start the app. However, you'll need to change a value in `avwx_account/config.py` to disable email authentication when creating new users.

```python
USER_ENABLE_EMAIL = False
```

## Runnng

If `FLASK_APP` is pointed to `avwx_account/__init__.py`, you can run the app using the Flask CLI.

```bash
flask run
```

## Deploy

The app is currently deployed on Heroku, so we need to have the `Procfile` for release and run. There's a quirk with Heroku's build pack that doesn't allow for gunicorn to point to an app within a package; the entire app 404s when called. Therefore, the production gunicorn pulls the app from `manage.py` which is currently the file's only use. This might change in the future, but for now it works.