import enum
from datetime import datetime

import click
import pytz
from flask import current_app
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Teacher(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(60), unique=True, nullable=False)


class Student(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    home_teacher_id = db.Column(db.String(60), db.ForeignKey('teacher.id'),
        nullable=False)
    home_teacher = db.relationship('Teacher', lazy=False)

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}'


class Block(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def upcoming():
        tz = pytz.timezone('US/Pacific')
        now = datetime.now(pytz.utc).astimezone(tz)
        midnight = datetime.combine(now.date(), datetime.min.time(), tz)
        return Block.query \
            .filter(Block.start_time >= midnight) \
            .order_by(Block.start_time.asc()) \
            .limit(10) \
            .all()


class Requester(enum.Enum):
    src = enum.auto()
    dst = enum.auto()
    auto = enum.auto()


class Request(db.Model):
    block_id = db.Column(db.Integer, db.ForeignKey('block.id'),
        nullable=False, primary_key=True)
    block = db.relationship('Block')
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'),
        nullable=False, primary_key=True)
    student = db.relationship('Student', lazy=False)
    destination_teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'),
        nullable=False)
    destination_teacher = db.relationship('Teacher', lazy=False)
    submitted_at = db.Column(db.DateTime, nullable=False)
    requester_code = db.Column(db.Enum(Requester), nullable=False)
    approved_at = db.Column(db.DateTime)

    @property
    def requester(self):
        if self.requester_code == Requester.src:
            return self.student.home_teacher
        elif self.requester_code == Requester.dst:
            return self.destination_teacher
        else:
            return None

    @property
    def approver(self):
        if self.requester_code == Requester.src:
            return self.destination_teacher
        elif self.requester_code == Requester.dst:
            return self.student.home_teacher
        else:
            return None

    @property
    def approved(self):
        return bool(self.approved_at)

    @staticmethod
    def approve(block_id, student_id):
        db.session.query(Request) \
            .filter_by(block_id=block_id, student_id=student_id) \
            .update({'approved_at': datetime.now(pytz.utc)})
        db.session.commit()

    # TODO: Soft deletion
    @staticmethod
    def delete(block_id, student_id):
        db.session.query(Request) \
            .filter_by(block_id=block_id, student_id=student_id) \
            .delete()
        db.session.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    click.echo(f"Initializing '{uri}'...")
    db.create_all()
    click.echo('Success.')


def register_commands(app):
    app.cli.add_command(init_db_command)
