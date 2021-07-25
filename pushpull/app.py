import os

from flask import Flask
from flask import render_template


def create_app():
    """Initializes the application.

    Config variables can be overridden in testing by passing a mapping
    via the `config` parameter. In production, they should be read from
    a file called `config.py` in the instance state directory (i.e.
    `instance/`).
    """
    app = Flask(__name__, instance_relative_config=True)

    # Init hardcoded config defaults
    # N.B. See https://docs.sqlalchemy.org/en/14/core/engines.html#sqlite
    db_uri = f"sqlite:///{os.path.join(app.instance_path, 'pushpull.sqlite')}"
    app.config.from_mapping(
        SECRET_KEY='notasecret',
        DEBUG=True,
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Load config overrides
    app.config.from_pyfile('config.py', silent=True)

    # Create instance directory if necessary
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Init database
    from pushpull.model import db
    db.init_app(app)

    from pushpull import model, teacher_dash
    model.register_commands(app)
    app.register_blueprint(teacher_dash.bp)

    return app
