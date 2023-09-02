import os

from pushpull.app import app
from pushpull.main import bp as main_bp
from pushpull.filters import register_filters
from pushpull.teacher_dash import bp as teacher_dash_bp


register_filters(app)
app.register_blueprint(main_bp)
app.register_blueprint(teacher_dash_bp)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
