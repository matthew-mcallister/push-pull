from flask import Blueprint, render_template, request
from werkzeug.exceptions import abort

from pushpull.model import *


bp = Blueprint('teacher_dash', __name__, url_prefix='/teacher')


@bp.route('/<int:teacher_id>/block/<int:block_id>', methods=['GET', 'POST'])
def dash(teacher_id, block_id):
    success = None
    if request.method == 'POST':
        if 'approve' in request.form:
            student_id = int(request.form['approve'])
            Request.approve(block_id, student_id)
            success = f'Approved request (SID {student_id})'
        elif 'delete' in request.form:
            student_id = int(request.form['delete'])
            Request.delete(block_id, student_id)
            success = f'Denied request (SID {student_id})'
        elif 'pull' in request.form:
            student_id = int(request.form['pull'])
            Student.pull(student_id, teacher_id, block_id)
            success = f'Pull requested (SID {student_id})'

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
    return render_template(
        'teacher_dash.html',
        current_teacher=current_teacher,
        block=block,
        blocks=blocks,
        entries=entries,
        success=success,
    )


@bp.route('/<int:teacher_id>/block/<int:block_id>/pull', methods=['GET', 'POST'])
def pull(teacher_id, block_id):
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
