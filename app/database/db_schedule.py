from flask_login import current_user
from sqlalchemy import desc
from app import db, log
from app.database import db_utils, db_setting
from app.database.models import Schedule, Teacher
import datetime

def dayhour_format_select(d, h):
    return ('{}/{}'.format(d, h), '{} : {}'.format(Schedule.WEEK_DAYS[d - 1], h))

def db_schedule_list(teacher=None, html_select=False):
    if html_select:
        q = db.session.query(Schedule.day, Schedule.hour)
    else:
        q = Schedule.query
    if teacher:
        q = q.join(Teacher).filter(Schedule.teacher == teacher)
    q_all = query_filter(q).distinct().order_by(Schedule.day, Schedule.hour).all()
    if html_select:
        l = [dayhour_format_select(d, h) for (d, h) in q_all]
        return l
    return q_all

def db_schedule_academic_year_list():
    academic_years = db.session.query(Schedule.academic_year).distinct().order_by(Schedule.academic_year).all()
    return [int(i) for i, in academic_years]


def query_filter(query_in):
    now = datetime.datetime.now()
    if db_setting.get_global_setting_sim_dayhour_state():
        try:
            now = datetime.datetime.strptime(db_setting.get_global_setting_sim_dayhour(), '%d-%m-%Y %H:%M')
        except Exception as e:
            pass
    schedule = Schedule.query.filter(Schedule.valid_from <= now).distinct().order_by(desc(Schedule.valid_from)).first()
    if not schedule:
        return query_in

    return query_in.filter(Schedule.school == db_utils.school(), Schedule.academic_year == db_utils.academic_year(), Schedule.valid_from == schedule.valid_from)

