from __future__ import annotations

import enum
from datetime import datetime
from datetime import date

import pytz
import sqlalchemy as sa
from sqlalchemy import MetaData, UniqueConstraint, orm
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from pushpull.app import app
from pushpull import errors


engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
factory = orm.sessionmaker(bind=engine)
session = orm.scoped_session(factory)

@app.teardown_request
def shutdown_request(*args, **kwargs):
    session.remove()


base = declarative_base(
    metadata=MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    ),
)
BaseModel = base


class Teacher(BaseModel):
    __tablename__ = 'teacher'

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(120))
    email: Mapped[str] = mapped_column(sa.String(60), unique=True)
    active: Mapped[bool] = mapped_column(sa.Boolean, default=True, server_default='true')

    students: Mapped[list[Student]] = relationship(
        'Student', secondary='assignment', viewonly=True)

    def __repr__(self) -> str:
        return f'<Teacher {self.id} "{self.name}">'

    @staticmethod
    def get(id: int) -> Teacher:
        teacher = session.query(Teacher).get(id)
        if not teacher:
            raise errors.NoSuchResource(f'No teacher with ID {id}')
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

    assignments: Mapped[list[Assignment]] = relationship(back_populates='student')
    requests: Mapped[list[Request]] = relationship(back_populates='student', lazy=True)

    def __repr__(self) -> str:
        return f'<Student {self.id} "{self.name}">'

    @property
    def name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    @staticmethod
    def get(id: int) -> Student:
        student = session.query(Student).get(id)
        if not student:
            raise errors.NoSuchResource(f'No student with ID {id}')
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


class Period(BaseModel):
    __tablename__ = 'period'

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(20))

    def __repr__(self) -> str:
        return self.name

    @staticmethod
    def get_by_name(name: str) -> Period:
        period = session.query(Period).filter_by(name=name).first()
        if not period:
            raise errors.NoSuchResource(f'No period named {name}')
        return period


class Assignment(BaseModel):
    __tablename__ = 'assignment'

    student_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey('student.id'), primary_key=True)
    student: Mapped[Student] = relationship(back_populates='assignments')
    period_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey('period.id'), primary_key=True)
    period: Mapped[Period] = relationship()
    teacher_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey('teacher.id'))
    teacher: Mapped[Teacher] = relationship(lazy=False)

    @staticmethod
    def get(student: Student, period: Period) -> Assignment:
        asn = session.query(Assignment).get((student.id, period.id))
        if not asn:
            raise errors.NoSuchResource(f'No assignment for {student}, period {period}')
        return asn


class Block(BaseModel):
    __tablename__ = 'block'

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    day: Mapped[date] = mapped_column(sa.Date)
    period_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey('period.id'))
    period: Mapped[Period] = relationship()

    __table_args__ = (
        UniqueConstraint(day, period_id),
    )

    def __repr__(self) -> str:
        return f'<Block {self.id} "{self.day.strftime("%Y-%m-%d")} {self.period}">'

    @staticmethod
    def get(id: int) -> Block:
        block = session.query(Block).get(id)
        if not block:
            raise errors.NoSuchResource(f'No block {id}')
        return block

    @staticmethod
    def get_by_day_and_period(day: date, period: Period) -> Block:
        block = session.query(Block).filter_by(day=day, period=period).first()
        if not block:
            raise errors.NoSuchResource(f'No block for {day}, period {period}')
        return block

    @staticmethod
    def upcoming() -> list[Block]:
        today = date.today()
        return session.query(Block) \
            .filter(Block.day >= today) \
            .order_by(Block.day.asc(), Block.period_id.asc()) \
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
    approved_at: Mapped[datetime] = mapped_column(sa.DateTime, nullable=True)

    @staticmethod
    def get(id: int) -> Request:
        request = session.query(Request).get(id)
        if not request:
            raise errors.NoSuchResource(f'No request with ID {id}')
        return request

    @property
    def source_teacher(self) -> Teacher | None:
        return (
            session.query(Teacher)
            .select_from(Request)
            .filter_by(student_id=self.student_id, block_id=self.block_id)
            .join(Block, Request.block_id == Block.id)
            .join(Assignment, sa.and_(Assignment.period_id == Block.period_id, Assignment.student_id == Request.student_id))
            .join(Teacher, Teacher.id == Assignment.teacher_id)
            .first()
        )

    @property
    def requester(self) -> Teacher | None:
        if self.requester_code == Requester.src:
            return self.source_teacher
        elif self.requester_code == Requester.dst:
            return self.destination_teacher
        else:
            return None

    @property
    def approver(self) -> Teacher | None:
        if self.requester_code == Requester.src:
            return self.destination_teacher
        elif self.requester_code == Requester.dst:
            return self.source_teacher
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

    @staticmethod
    def delete(block_id: int, student_id: int) -> None:
        session.query(Request) \
            .filter_by(block_id=block_id, student_id=student_id) \
            .delete()
        session.commit()

    @property
    def assigned_teacher(self) -> Teacher | None:
        asn = Assignment.get(self.student, self.block.period)
        if asn:
            return asn.teacher
        else:
            return None
