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
        'test_view.html',
        current_teacher=current_teacher,
    )


@bp.route('/dash')
def dash():
    raise NotImplementedError()
