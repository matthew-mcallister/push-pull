import os
from typing import Any

from dotenv import load_dotenv
from flask import Flask
from flask import render_template
from flask import request
from flask import Response


def _create_app() -> Flask:
    """Initializes the application.

    Config variables can be overridden in testing by passing a mapping
    via the `config` parameter. In production, they should be read from
    a file called `config.py` in the instance state directory (i.e.
    `instance/`).
    """
    app = Flask(__name__, instance_relative_config=True)

    load_dotenv()

    db_url = os.environ['DATABASE_URL']
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    secret = os.getenv('FLASK_SECRET_KEY', 'notasecret')

    app.config.from_mapping(
        SECRET_KEY=secret,
        DEBUG=True,
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Load config overrides
    app.config.from_pyfile('config.py', silent=True)

    from pushpull import aeries, filters, main, model, teacher_dash
    model.db.init_app(app)
    aeries.register_commands(app)
    model.register_commands(app)
    filters.register_filters(app)

    app.register_blueprint(main.bp)
    app.register_blueprint(teacher_dash.bp)

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

    return app


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    @app.route('/')
    def redirect():
        return render_template('redirect.html')

    return app


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    create_app().run(debug=True, host='0.0.0.0', port=port)
