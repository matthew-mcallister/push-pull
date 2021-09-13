import pytz


def utc_to_local(value, format):
    new = value.astimezone(pytz.timezone('US/Pacific'))
    return new.strftime(format)


def register_filters(app):
    app.jinja_env.filters['utc_to_local'] = utc_to_local
