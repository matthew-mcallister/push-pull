import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask
from flask import request
from flask import Response
from flask import abort

from pushpull import errors


app = Flask(__name__, instance_relative_config=True)

path = os.getenv('DOTENV')
load_dotenv(Path(path).resolve() if path else None)

db_url = os.environ['DATABASE_URL']
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

secret = os.getenv('FLASK_SECRET_KEY', 'notasecret')

app.config.from_mapping(
    SECRET_KEY=secret,
    SQLALCHEMY_DATABASE_URI=db_url,
)

# Load config overrides
app.config.from_pyfile('config.py', silent=True)


@app.before_request
def auth() -> Any:
    required_password = os.getenv('HTTP_PASSWORD')
    if not required_password:
        return

    def fail() -> Any:
        resp = Response('Authorization required', 401)
        resp.headers['WWW-Authenticate'] = 'Basic'
        return resp

    auth = request.authorization
    if not auth or not auth.password or auth.password != required_password:
        return fail()


@app.errorhandler(errors.ErrorBase)
def handle_error(e: errors.ErrorBase):
    abort(e.status_code)
