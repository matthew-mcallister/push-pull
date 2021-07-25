import dataclasses
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template


bp = Blueprint('teacher_dash', __name__, url_prefix='/teacher')


# PLACEHOLDER TYPES AND DATA

@dataclass(eq=False)
class Teacher:
    id: int
    name: str


TEACHERS = {
    0: Teacher(id=0, name='Rachel LaFein'),
    1: Teacher(id=1, name='Jennifer Sprague'),
    2: Teacher(id=2, name='Paul York'),
    3: Teacher(id=3, name='Bob Cunningham'),
    4: Teacher(id=4, name='Daniel Rupp'),
    5: Teacher(id=5, name='Bob Anderson'),
}


@dataclass(eq=False)
class Student:
    id: int
    first_name: str
    last_name: str
    teacher: Teacher
    request: 'Request' = None

    @property
    def name(self):
        return f'{self.first_name} {self.last_name}'


STUDENTS = {
    13001: Student(id=13001, first_name='Joe', last_name='Schmoe', teacher=TEACHERS[0]),
    13002: Student(id=13002, first_name='Jane', last_name='Schmane', teacher=TEACHERS[0]),
    13003: Student(id=13003, first_name='John', last_name='Schmon', teacher=TEACHERS[0]),
    13004: Student(id=13004, first_name='Joan', last_name='Schmoan', teacher=TEACHERS[0]),
    13005: Student(id=13005, first_name='Jim', last_name='Schmim', teacher=TEACHERS[0]),
    13006: Student(id=13006, first_name='Jean', last_name='Schmean', teacher=TEACHERS[3]),
    13007: Student(id=13007, first_name='Jed', last_name='Schmed', teacher=TEACHERS[4]),
    13008: Student(id=13008, first_name='Janet', last_name='Schmanet', teacher=TEACHERS[0]),
    13009: Student(id=13009, first_name='Jill', last_name='Schmill', teacher=TEACHERS[5]),
}


@dataclass(eq=False)
class Request:
    id: int
    student: Student
    destination: Teacher
    request_code: str
    approved: bool
    time_submitted: datetime = datetime.now()
    cycle: int = 0
    block: int = 0

    @property
    def requester(self):
        if self.request_code == 'S':
            return self.student.teacher
        elif self.request_code == 'D':
            return self.destination
        else:
            return None

    @property
    def approver(self):
        if self.request_code == 'S':
            return self.destination
        elif self.request_code == 'D':
            return self.student.teacher
        else:
            return None


REQUESTS = [
    Request(id=0, student=STUDENTS[13002], destination=TEACHERS[2], request_code='D', approved=False),
    Request(id=1, student=STUDENTS[13003], destination=TEACHERS[1], request_code='S', approved=True),
    Request(id=2, student=STUDENTS[13006], destination=TEACHERS[0], request_code='S', approved=True),
    Request(id=3, student=STUDENTS[13007], destination=TEACHERS[0], request_code='D', approved=False),
    Request(id=4, student=STUDENTS[13009], destination=TEACHERS[0], request_code='A', approved=False),
]

@bp.route('/dash')
def dash():
    current_teacher = TEACHERS[0]
    hr_students = [
        student
        for student in STUDENTS.values()
        if student.teacher == current_teacher
    ]
    hr_student_ids = [student.id for student in hr_students]
    requests_by_stu = {
        request.student.id: request
        for request in REQUESTS
        if (request.student.id in hr_student_ids
            or request.destination == current_teacher)
    }
    visiting_students = [
        request.student
        for request in requests_by_stu.values()
        if request.destination == current_teacher
    ]
    students = hr_students + visiting_students
    # Crappy attempt at a join
    for i, student in enumerate(students):
        try:
            students[i] = dataclasses.replace(student, request=requests_by_stu[student.id])
        except KeyError:
            pass
    students.sort(key=lambda stu: stu.last_name)
    return render_template(
        'teacher_dash.html',
        app_title="Push 'n' Pull",
        current_teacher=current_teacher,
        teachers=list(TEACHERS.values()),
        students=students,
    )
