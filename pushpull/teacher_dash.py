from flask import abort
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import session as flask_session
from flask import url_for

from pushpull.model import *


bp = Blueprint('teacher_dash', __name__, url_prefix='/teacher')


@bp.route('/<int:teacher_id>/block/<int:block_id>/')
def dash(teacher_id: int, block_id: int):
    current_teacher = session.query(Teacher).get(teacher_id)
    if not current_teacher:
        abort(404)
    block = session.query(Block).get(block_id)
    if not block:
        abort(404)
    blocks = Block.upcoming()
    entries = session.query(Student) \
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
        alert=flask_session.get('alert'),
        status=flask_session.get('status'),
        teachers=session.query(Teacher).all(),
    )
    flask_session.clear()
    return result


@bp.route('/<int:teacher_id>/block/<int:block_id>/pull/')
def pull(teacher_id: int, block_id: int):
    current_teacher = session.query(Teacher).get(teacher_id)
    if not current_teacher:
        abort(404)
    block = session.query(Block).get(block_id)
    if not block:
        abort(404)
    query = session.query(Student, Request) \
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


@bp.route('/<int:teacher_id>/block/<int:block_id>/action/', methods=['POST'])
def action(teacher_id: int, block_id: int):
    status = 'success'
    alert = None
    if 'approve' in request.form:
        student_id = int(request.form['approve'])
        Request.approve(block_id, student_id)
        alert = f'Approved request (SID {student_id})'
    elif 'delete' in request.form:
        student_id = int(request.form['delete'])
        Request.delete(block_id, student_id)
        alert = f'Denied request (SID {student_id})'
    elif 'pull' in request.form:
        student_id = int(request.form['pull'])
        Student.pull(student_id, teacher_id, block_id)
        alert = f'Pull requested (SID {student_id})'
    elif 'push' in request.form:
        if not request.form['teacher']:
            status = 'info'
            alert = 'You must select a teacher to push to.'
        else:
            student_id = int(request.form['push'])
            dst_teacher_id = int(request.form['teacher'])
            Student.push(student_id, dst_teacher_id, block_id)
            alert = f'Push requested (SID {student_id})'
    flask_session['status'] = status
    if alert:
        flask_session['alert'] = alert
    url = url_for('.dash', teacher_id=teacher_id, block_id=block_id)
    return redirect(url, code=303)
