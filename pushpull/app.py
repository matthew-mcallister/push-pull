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

    db_url = os.getenv('DATABASE_URL')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config.from_mapping(
        SECRET_KEY='notasecret',
        DEBUG=True,
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Load config overrides
    app.config.from_pyfile('config.py', silent=True)

    # Create instance directory if necessary
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from pushpull import aeries, model, teacher_dash
    model.db.init_app(app)
    model.register_commands(app)
    aeries.register_commands(app)
    app.register_blueprint(teacher_dash.bp)

    return app


if __name__ == '__main__':
    create_app().run(debug=True)
