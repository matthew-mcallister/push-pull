from datetime import datetime

from flask import Blueprint, render_template
from sqlalchemy import and_, or_
from werkzeug.exceptions import abort

from pushpull.model import *


bp = Blueprint('teacher_dash', __name__, url_prefix='/teacher')


@bp.route('/<int:teacher_id>/block/<int:block_id>')
def dash(teacher_id, block_id):
    current_teacher = Teacher.query.get_or_404(teacher_id)
    block = Block.query.get_or_404(block_id)
    entries = Student.query \
        .outerjoin(Request, and_(
            Request.student_id == Student.id,
            Request.block_id == block_id,
        )) \
        .filter(or_(
            Student.home_teacher_id == teacher_id,
            Request.destination_teacher_id == teacher_id,
        )) \
        .add_entity(Request) \
        .all()
    return render_template(
        'teacher_dash.html',
        app_title='Push<->Pull',
        current_teacher=current_teacher,
        block=block,
        entries=entries,
    )
