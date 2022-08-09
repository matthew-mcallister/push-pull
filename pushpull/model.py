import enum
from datetime import datetime

import click
import pytz
from flask import current_app
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Teacher(db.Model):
    id: int = db.Column(db.Integer, nullable=False, primary_key=True)
    name: str = db.Column(db.String(120), nullable=False)
    email: str = db.Column(db.String(60), unique=True, nullable=False)

    @staticmethod
    def all_by_name():
        return Teacher.query.order_by(Teacher.name.asc()).all()


class Student(db.Model):
    id: int = db.Column(db.Integer, nullable=False, primary_key=True)
    first_name: str = db.Column(db.String(60), nullable=False)
    last_name: str = db.Column(db.String(60), nullable=False)
    home_teacher_id: int = db.Column(db.Integer, db.ForeignKey('teacher.id'),
        nullable=False)
    home_teacher: Teacher = db.relationship('Teacher', lazy=False)

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}'

    @staticmethod
    def pull(student_id: int, teacher_id: int, block_id: int):
        db.session.add(Request(
            block_id=block_id,
            student_id=student_id,
            destination_teacher_id=teacher_id,
            submitted_at=datetime.now(pytz.utc),
            requester_code=Requester.dst,
            approved_at=None,
        ))
        db.session.commit()

    @staticmethod
    def push(student_id: int, teacher_id: int, block_id: int):
        db.session.add(Request(
            block_id=block_id,
            student_id=student_id,
            destination_teacher_id=teacher_id,
            submitted_at=datetime.now(pytz.utc),
            requester_code=Requester.src,
            approved_at=None,
        ))
        db.session.commit()


class Block(db.Model):
    id: int = db.Column(db.Integer, nullable=False, primary_key=True)
    start_time: datetime = db.Column(db.DateTime, nullable=False)

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
    block_id: int = db.Column(db.Integer, db.ForeignKey('block.id'),
        nullable=False, primary_key=True)
    block: Block = db.relationship('Block')
    student_id: int = db.Column(db.Integer, db.ForeignKey('student.id'),
        nullable=False, primary_key=True)
    student: Student = db.relationship('Student', lazy=False)
    destination_teacher_id: int = db.Column(db.Integer, db.ForeignKey('teacher.id'),
        nullable=False)
    destination_teacher: Teacher = db.relationship('Teacher', lazy=False)
    submitted_at: datetime = db.Column(db.DateTime, nullable=False)
    requester_code = db.Column(db.Enum(Requester), nullable=False)
    approved_at: datetime = db.Column(db.DateTime)

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
    def approve(block_id: int, student_id: int):
        db.session.query(Request) \
            .filter_by(block_id=block_id, student_id=student_id) \
            .update({'approved_at': datetime.now(pytz.utc)})
        db.session.commit()

    # TODO: Soft deletion
    @staticmethod
    def delete(block_id: int, student_id: int):
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
