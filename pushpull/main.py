from flask import Blueprint, render_template

from pushpull.model import *


bp = Blueprint('main', __name__, url_prefix='/')


@bp.route('/')
def home():
    return render_template(
        'home.html',
        app_title='Push<->Pull',
        block=Block.upcoming()[0],
        teachers=Teacher.query.all(),
    )
