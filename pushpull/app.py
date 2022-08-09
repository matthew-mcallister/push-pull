import os

from dotenv import load_dotenv
from flask import Flask


def create_app():
    """Initializes the application.

    Config variables can be overridden in testing by passing a mapping
    via the `config` parameter. In production, they should be read from
    a file called `config.py` in the instance state directory (i.e.
    `instance/`).
    """
    app = Flask(__name__, instance_relative_config=True)

    load_dotenv()

    db_url = os.getenv('DATABASE_URL')
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

    return app


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    create_app().run(debug=True, host='0.0.0.0', port=port)
