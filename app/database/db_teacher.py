from sqlalchemy import func

from app.database import db_utils, db_schedule
from app import db
from app.database.models import Teacher, Schedule
from app.utils import utils


def db_teacher_list(select=False):
    if select:
        q = db.session.query(Teacher.id, Teacher.code)
    else:
        q = Teacher.query
    return db_schedule.query_filter(q.join(Schedule)).distinct().order_by(Teacher.code).all()

def db_teacher(id=None, code=None):
    if id:
        return Teacher.query.get(id)
    elif code:
        return Teacher.query.filter(Teacher.code == func.binary(code)).first()