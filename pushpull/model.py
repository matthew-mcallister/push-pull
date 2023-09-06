from __future__ import annotations

import enum
from datetime import datetime

import pytz
import sqlalchemy as sa
from flask import abort
from flask import request
from sqlalchemy import orm
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from pushpull.app import app


engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
factory = orm.sessionmaker(bind=engine)
session = orm.scoped_session(factory)

@app.teardown_request
def shutdown_request(*args, **kwargs):
    session.remove()


base = declarative_base()


BaseModel = base


class Teacher(BaseModel):
    __tablename__ = 'teacher'

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(120))
    email: Mapped[str] = mapped_column(sa.String(60), unique=True)
    active: Mapped[bool] = mapped_column(sa.Boolean, default=True, server_default='true')

    @staticmethod
    def get(id: int) -> Teacher:
        teacher = session.query(Teacher).get(id)
        if not teacher:
            abort(404)
        return teacher

    @staticmethod
    def all_by_name() -> list[Teacher]:
        return (
            session.query(Teacher)
                .filter_by(active=True)
                .order_by(Teacher.name.asc())
                .all()
        )


class Student(BaseModel):
    __tablename__ = 'student'

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(sa.String(60))
    last_name: Mapped[str] = mapped_column(sa.String(60))
    home_teacher_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey('teacher.id'))
    home_teacher: Mapped[Teacher] = relationship(lazy=False)

    @property
    def name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    @staticmethod
    def get(id: int) -> Student:
        student = session.query(Student).get(id)
        if not student:
            abort(404)
        return student

    @staticmethod
    def pull(student_id: int, teacher_id: int, block_id: int) -> None:
        session.add(Request(
            block_id=block_id,
            student_id=student_id,
            destination_teacher_id=teacher_id,
            submitted_at=datetime.now(pytz.utc),
            requester_code=Requester.dst,
            approved_at=None,
        ))
        session.commit()

    @staticmethod
    def push(student_id: int, teacher_id: int, block_id: int) -> None:
        session.add(Request(
            block_id=block_id,
            student_id=student_id,
            destination_teacher_id=teacher_id,
            submitted_at=datetime.now(pytz.utc),
            requester_code=Requester.src,
            approved_at=None,
        ))
        session.commit()


class Block(BaseModel):
    __tablename__ = 'block'

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    start_time: Mapped[datetime] = mapped_column(sa.DateTime)

    @staticmethod
    def get(id: int) -> Block:
        block = session.query(Block).get(id)
        if not block:
            abort(404)
        return block

    @staticmethod
    def upcoming() -> list[Block]:
        tz = pytz.timezone('US/Pacific')
        now = datetime.now(pytz.utc).astimezone(tz)
        midnight = datetime.combine(now.date(), datetime.min.time(), tz)
        return session.query(Block) \
            .filter(Block.start_time >= midnight) \
            .order_by(Block.start_time.asc()) \
            .limit(10) \
            .all()


class Requester(enum.Enum):
    src = enum.auto()
    dst = enum.auto()
    auto = enum.auto()


class Request(BaseModel):
    __tablename__ = 'request'

    block_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey('block.id'), primary_key=True)
    block: Mapped[Block] = relationship()
    student_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey('student.id'), primary_key=True)
    student: Mapped[Student] = relationship(lazy=False)
    destination_teacher_id: Mapped[int] = mapped_column(
        sa.Integer, sa.ForeignKey('teacher.id'))
    destination_teacher: Mapped[Teacher] = relationship(lazy=False)
    submitted_at: Mapped[datetime] = mapped_column(sa.DateTime)
    requester_code: Mapped[Requester] = mapped_column(sa.Enum(Requester))
    approved_at: Mapped[datetime] = mapped_column(sa.DateTime)

    @staticmethod
    def get(id: int) -> Request:
        request = session.query(Request).get(id)
        if not request:
            abort(404)
        return request

    @property
    def requester(self) -> Teacher | None:
        if self.requester_code == Requester.src:
            return self.student.home_teacher
        elif self.requester_code == Requester.dst:
            return self.destination_teacher
        else:
            return None

    @property
    def approver(self) -> Teacher | None:
        if self.requester_code == Requester.src:
            return self.destination_teacher
        elif self.requester_code == Requester.dst:
            return self.student.home_teacher
        else:
            return None

    @property
    def approved(self) -> bool:
        return bool(self.approved_at)

    @staticmethod
    def approve(block_id: int, student_id: int) -> None:
        session.query(Request) \
            .filter_by(block_id=block_id, student_id=student_id) \
            .update({'approved_at': datetime.now(pytz.utc)})
        session.commit()

    # TODO: Soft deletion
    @staticmethod
    def delete(block_id: int, student_id: int) -> None:
        session.query(Request) \
            .filter_by(block_id=block_id, student_id=student_id) \
            .delete()
        session.commit()
