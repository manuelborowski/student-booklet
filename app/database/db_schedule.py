import app.database.db_utils
from app import db
from app.utils import utils
from app.database.models import Schedule, Teacher


def db_schedule_list(teacher=None, select=False):
    if select:
        q = db.session.query(Schedule.day, Schedule.hour)
    else:
        q = Schedule.query
    if teacher:
        q = q.join(Teacher).filter(Schedule.teacher == teacher)
    q_all = q.filter(Schedule.school == app.database.db_utils.school(), Schedule.academic_year == app.database.db_utils.academic_year())\
        .distinct().order_by(Schedule.day, Schedule.hour).all()
    if select:
        l = [('{}/{}'.format(d, h), '{} : {}'.format(Schedule.WEEK_DAYS[d - 1], h)) for (d, h) in q_all]
        return l
    return q_all

def db_schedule_academic_year_list():
    academic_years = db.session.query(Schedule.academic_year).distinct().order_by(Schedule.academic_year).all()
    return [int(i) for i, in academic_years]
