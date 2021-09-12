import enum

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Teacher(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)
    students = db.relationship('Student', backref='teacher', lazy=True)


class Student(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    home_teacher_id = db.Column(db.String(60), db.ForeignKey('teacher.id'),
        nullable=False)


class Block(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)


class Requester(enum.Enum):
    src = enum.auto()
    dst = enum.auto()
    auto = enum.auto()


class Request(db.Model):
    block_id = db.Column(db.Integer, db.ForeignKey('block.id'), nullable=False,
        primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'),
        nullable=False, primary_key=True)
    destination_teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'),
        nullable=False, primary_key=True)
    approved = db.Column(db.Boolean, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False)
    requester = db.Column(db.Enum(Requester), nullable=False)

    @property
    def requester(self):
        if self.requester == Requester.src:
            return self.student.teacher
        elif self.requester == Requester.dst:
            return self.destination
        else:
            return None

    @property
    def approver(self):
        if self.requester == Requester.src:
            return self.destination
        elif self.requester == Requester.dst:
            return self.student.teacher
        else:
            return None


@click.command('init-db')
@with_appcontext
def init_db_command():
    uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    click.echo(f"Initializing '{uri}'...")
    db.create_all()
    click.echo('Success.')


def register_commands(app):
    app.cli.add_command(init_db_command)
