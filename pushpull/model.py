import click
from flask import current_app
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f"Teacher({self.id}, {self.name})"


@click.command('init-db')
@with_appcontext
def init_db_command():
    uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    click.echo(f"Initializing '{uri}'...")
    db.create_all()
    click.echo('Success.')


def register(app):
    app.cli.add_command(init_db_command)
