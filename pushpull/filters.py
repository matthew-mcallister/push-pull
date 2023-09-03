from datetime import datetime

import pytz
from flask import Flask


def utc_to_local(value: datetime, format: str):
    value = pytz.utc.localize(value)
    new = value.astimezone(pytz.timezone('US/Pacific'))
    return new.strftime(format)


def register_filters(app: Flask):
    app.jinja_env.filters['utc_to_local'] = utc_to_local
