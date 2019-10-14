# -*- coding: utf-8 -*-

# app/__init__.py

# third-party imports
from flask import Flask, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_jsglue import JSGlue
from werkzeug.routing import IntegerConverter as OrigIntegerConvertor
from werkzeug.contrib.profiler import ProfilerMiddleware
import logging.handlers, os, sys
from functools import wraps

app = Flask(__name__, instance_relative_config=True)


# V1.0 : base version, everything works
# V1.1 : remarksubjects and remarkmeasures : they are stored in the database and can be appended
# V1.2 : reworked and refactored html-pages to view single items
# V1.3 : new user : email is not required
# V1.4 : debugged schedule, added simulate schedule, refactored settings
# V1.5 : bugifx : submit of user-details did not work anymore
# V1.6 : upgrade to python 3.7.2  Filter of muliple items works differently
# V1.7 : bugfix not compatible mysql connector
# V1.8 : esthetical upgrade in login screen
# v1.9 : python 2 to 3 : zip() to list(zip())
# V2.0 : local updated copy of bootstrap
# V2.1 : switched to nginx
# V2.2 : bugfix timeslot-selecting-scheme.  User cannot delete itself
# V2.3 : bugfix : mobile safari and chrome : submit button does not work correctly
# V2.4 : update background image, added extra_attention flag in database
# V2.5 : increment version
# V2.6 : esthetical improvement.  During review, extra-attention-remarks are collored
# V2.7 : esthetical improvement
# V2.8 : esthetical improvement.  Bugfixed footer and autologout
# V2.9 : esthetical improvement : add a color legend.  Add more colors to show the status of a remark
# V2.10 : esthetical improvement
# V2.11 : import students, teachers and timetable direct from export
# V2.12 : esthetical improvement
# V2.13 : bugfix column order in case of table with row_detail.  Esthetical improvements
# V2.14 : row_detail : get row_detail data via ajax only when required
# V2.15 : speed improvement ; switched to correct sql statements
# V2.16 : bugfix upload students
# V2.17 : small refactoring
# V2.18 : huge refactor
# V2.19 : implemented logic to handle valid_from in schedule.
# V2.20 : teacher table has a school-column now
# V2.21 : add/edit/remove substitute teachers, reworked settings
# V2.22 : substitute teachers are implemented
# V2.23 : reworked legend
# V2.24 : if substitute teacher adds a remark, the remark is associated with the substitute teacherµ
# V2.25 : small bugfixes
# V2.26 : issue with creating/upgrading the database
# V2.27 : create index on schedule table
# V2.28 : replacement teacher list : added full name
# V2.29 : update of packages : sqlalchemy and urllib3
# V2.30 : bugfixed a query to improve speed
# V2.31 : added indication for test-server.  Bugfixed grade-button : button-pressed was not present in request
# V2.32 : allow oath users with small letters.  Remarks list : default sort on date descending
# V2.33 : added classgroup table
# V2.34 : bugfix due to added classgroup table
# V2.35 : when adding a remark, the program tries to guess the correct date.  The date can be altered, if required
# V2.36 : truncate classgrouplist if it's longer than 40 characters
# V2.37 : show current values when editing a remark
# V2.38 : truncate text if it is longer than 60 characters.  Schow complete text in tooltip
# V2.39 : timestamp is saved as date and hour (stored in seconds).  Backwards compatible with current timestamp
# V2.40 : duplicate remarks (same student, same hour) are merged
# V2.41 : during review, it is possible to postpone review of a set of remarks
# V2.42 : bugifx : measure_note and remark_note must not be None.  When a remark was being edit, it always gave a warning
# V2.43 : introduced a website maintenance page
# V2.44 : bugfix : forgot maintanance page
# V2.45 : simplified datatables : first stage is faster, added functions in database, escape html codes.  Webserver : single process/thread
# V2.46 : refactor
# V2.27 : html : apply academic-year-filter when navigating to the remarks-page
# V2.48 : student export from wisa : use API stdntmapje
# V2.49 : hidden students are not displayed anymore
# v2.50 : full student name : last name plus first name.  Debugged searching for student name
# V2.51 : added database_functions.txt file
# V2.52 : admin only : add a button to hide students
# V2.53 : reviewed remarks : students name in correct order : surname + firstname
# V2.54 : added generic teacher XXXX with all grades.  Non teachers can now create remarks as well
# V2.55 : bugfix
# V2.56 : bugfix
# V2.57 : added settings/generic page for generic settings.  Added configurable link to help page
# V2.58 : make it possible to search in measures and topics
# V2.59 : added help files
# V2.60 : added nginx file for help website
# V2.61 : bugfix extra measures : search on student name and extra measure
# V2.62 : extra measure : default order table on date, descending
# V2.63 : extra measure : line details : sorted by date descending

@app.context_processor
def inject_version():
    return dict(version='V2.63')


# enable logging
LOG_HANDLE = 'SB'
log = logging.getLogger(LOG_HANDLE)

# local imports
from config import app_config

db = SQLAlchemy()
login_manager = LoginManager()


# The original werkzeug-url-converter cannot handle negative integers (e.g. asset/add/-1/1)
class IntegerConverter(OrigIntegerConvertor):
    regex = r'-?\d+'
    num_convert = int


# support custom filtering while logging
class MyLogFilter(logging.Filter):
    def filter(self, record):
        record.username = current_user.username if current_user and current_user.is_active else 'NONE'
        return True


config_name = os.getenv('FLASK_CONFIG')
config_name = config_name if config_name else 'production'

# set up logging
LOG_FILENAME = os.path.join(sys.path[0], app_config[config_name].STATIC_PATH, 'log/sb-log.txt')
try:
    log_level = getattr(logging, app_config[config_name].LOG_LEVEL)
except:
    log_level = getattr(logging, 'INFO')
log.setLevel(log_level)
log.addFilter(MyLogFilter())
log_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10 * 1024, backupCount=5)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(username)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

log.info('start SB')

app.config.from_object(app_config[config_name])
app.config.from_pyfile('config.py')

Bootstrap(app)

jsglue = JSGlue(app)
db.app = app  # hack :-(
db.init_app(app)


def create_admin():
    from app.database.models import User
    admin = User(username='admin', password='admin', level=User.LEVEL.ADMIN, user_type=User.USER_TYPE.LOCAL)
    db.session.add(admin)
    db.session.commit()


app.url_map.converters['int'] = IntegerConverter

login_manager.init_app(app)
login_manager.login_message = 'Je moet aangemeld zijn om deze pagina te zien!'
login_manager.login_view = 'auth.login'

migrate = Migrate(app, db)

if 'db' in sys.argv:
    from app.database import models
else:
    # create_admin() # Only once

    # flask database migrate
    # flask database upgrade
    # uncheck when migrating database
    # return app

    # app.config['PROFILE'] = True
    # app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=['app', 0.8])

    # decorator to grant access to admins only
    def admin_required(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_at_least_admin:
                abort(403)
            return func(*args, **kwargs)

        return decorated_view


    # decorator to grant access to at least supervisors
    def supervisor_required(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_at_least_supervisor:
                abort(403)
            return func(*args, **kwargs)

        return decorated_view


    from app.view.grade import grade as grade_blueprint

    app.register_blueprint(grade_blueprint)

    from app.view.auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint)

    from app.view.settings import settings as settings_blueprint

    app.register_blueprint(settings_blueprint)

    from app.view.settings.replacements import replacements as replacements_blueprint

    app.register_blueprint(replacements_blueprint)

    from app.view.user import user as user_blueprint

    app.register_blueprint(user_blueprint)

    from app.view.remarks import remarks as remarks_blueprint

    app.register_blueprint(remarks_blueprint)

    from app.view.reviewed import reviewed as reviewed_blueprint

    app.register_blueprint(reviewed_blueprint)

    from app.utils.documents import init_documents

    init_documents(app, 'photo')


    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html', title='Forbidden'), 403


    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html', title='Page Not Found'), 404


    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html', title='Server Error'), 500


    @app.route('/500')
    def error_500():
        abort(500)
