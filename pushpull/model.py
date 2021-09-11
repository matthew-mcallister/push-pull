import dataclasses
from dataclasses import dataclass
from datetime import datetime

from flask import Blueprint, render_template

from pushpull.model import *


bp = Blueprint('teacher_dash', __name__, url_prefix='/teacher')


@bp.route('/test')
def test():
    current_teacher = Teacher.query.filter_by(username='rlafein').first()
    return render_template(
        'test.html',
    )


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
