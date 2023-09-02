from flask import Blueprint, render_template

from pushpull.model import *


bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/')
def home():
    return render_template(
        'home.html',
        block=Block.upcoming()[0],
        teachers=Teacher.all_by_name(),
    )
