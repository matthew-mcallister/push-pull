from datetime import datetime

from flask import Blueprint, render_template, request
from sqlalchemy import and_, or_
from werkzeug.exceptions import abort

from pushpull.model import *


bp = Blueprint('teacher_dash', __name__, url_prefix='/teacher')


@bp.route('/<int:teacher_id>/block/<int:block_id>', methods=['GET', 'POST'])
def dash(teacher_id, block_id):
    success = None
    if request.method == 'POST':
        if request.content_length > 1e5:
            abort(413)
        if 'approve' in request.form:
            student_id = int(request.form['approve'])
            Request.approve(block_id, student_id)
            success = f'Approved request for {student_id}'
        elif 'delete' in request.form:
            student_id = int(request.form['delete'])
            Request.delete(block_id, student_id)
            success = f'Denied request for {student_id}'
        else:
            abort(400)

    current_teacher = Teacher.query.get_or_404(teacher_id)
    block = Block.query.get_or_404(block_id)
    blocks = Block.upcoming()
    entries = Student.query \
        .outerjoin(Request, and_(
            Request.student_id == Student.id,
            Request.block_id == block_id,
        )) \
        .filter(or_(
            Student.home_teacher_id == teacher_id,
            Request.destination_teacher_id == teacher_id,
        )) \
        .order_by(Student.last_name) \
        .add_entity(Request) \
        .all()
    return render_template(
        'teacher_dash.html',
        app_title='Push<->Pull',
        current_teacher=current_teacher,
        block=block,
        blocks=blocks,
        entries=entries,
        success=success,
    )
