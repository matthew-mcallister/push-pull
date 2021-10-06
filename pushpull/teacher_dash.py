from functools import wrap

from flask import Blueprint, redirect, render_template, request, session, \
    url_for
from werkzeug.exceptions import abort

from pushpull.model import *


bp = Blueprint('teacher_dash', __name__, url_prefix='/teacher')


@bp.route('/<int:teacher_id>/block/<int:block_id>/')
def dash(teacher_id: int, block_id: int):
    current_teacher = Teacher.query.get_or_404(teacher_id)
    block = Block.query.get_or_404(block_id)
    blocks = Block.upcoming()
    entries = Student.query \
        .outerjoin(Request, (Request.student_id == Student.id) &
            (Request.block_id == block_id)) \
        .filter((Student.home_teacher_id == teacher_id) |
            (Request.destination_teacher_id == teacher_id)) \
        .order_by(Student.last_name) \
        .add_entity(Request) \
        .all()
    result = render_template(
        'teacher_dash.html',
        current_teacher=current_teacher,
        block=block,
        blocks=blocks,
        entries=entries,
        alert=session.get('alert'),
        status=session.get('status'),
        teachers=Teacher.query.all(),
    )
    session.clear()
    return result


@bp.route('/<int:teacher_id>/block/<int:block_id>/pull/')
def pull(teacher_id: int, block_id: int):
    current_teacher = Teacher.query.get_or_404(teacher_id)
    block = Block.query.get_or_404(block_id)
    query = db.session.query(Student, Request) \
        .outerjoin(Request, (Request.student_id == Student.id) &
            (Request.block_id == block_id)) \
        .filter(Student.home_teacher_id != teacher_id) \

    try:
        s = '%' + request.args['search'] + '%'
        query = query.filter(Student.first_name.ilike(s) |
            Student.last_name.ilike(s))
    except KeyError:
        pass

    entries = query.order_by(Student.last_name).all()
    return render_template(
        'pull.html',
        current_teacher=current_teacher,
        block=block,
        entries=entries,
    )


def teacher_action(f):
    @wraps(f)
    def inner(*args, **kwargs):
        teacher_id = args[0]
        block_id = args[1]
        session['status'] = 'success'
        # TODO: handle exceptions?
        f(teacher_id, block_id, *args, **kwargs)
        url = url_for('.dash', teacher_id=teacher_id, block_id=block_id)
        return redirect(url, code=303)
    return inner


@bp.route('/<int:teacher_id>/block/<int:block_id>/action/approve/<int:student_id>', methods=['POST'])
@teacher_action
def approve_action(teacher_id: int, block_id: int, student_id: int):
    Request.approve(block_id, student_id)
    session['alert'] = f'Approved request (SID {student_id})'


@bp.route('/<int:teacher_id>/block/<int:block_id>/action/delete/<int:student_id>', methods=['POST'])
@teacher_action
def delete_action(teacher_id: int, block_id: int, student_id: int):
    Request.delete(block_id, student_id)
    session['alert'] = f'Denied request (SID {student_id})'


@bp.route('/<int:teacher_id>/block/<int:block_id>/action/approve/<int:student_id>', methods=['POST'])
@teacher_action
def pull_action(teacher_id: int, block_id: int, student_id: int):
    Student.pull(student_id, teacher_id, block_id)
    session['alert'] = f'Pull requested (SID {student_id})'


@bp.route('/<int:teacher_id>/block/<int:block_id>/action/push/<int:student_id>/dest/<int:dest_teacher_id>', methods=['POST'])
@teacher_action
def push_action(
    teacher_id: int,
    block_id: int,
    student_id: int,
    dest_teacher_id: int,
):
    Student.push(student_id, dest_teacher_id, block_id)
    session['alert'] = f'Push requested (SID {student_id})'
