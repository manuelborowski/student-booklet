from sqlalchemy import func

from app.database import db_utils, db_schedule
from app import db
from app.database.models import Teacher, Schedule
from app.utils import utils


def db_teacher_list(select=False, schedule=True, full_name=False, id_list=None):
    if select:
        if full_name:
            q = db.session.query(Teacher.id, Teacher.code, Teacher.first_name, Teacher.last_name)
        else:
            q = db.session.query(Teacher.id, Teacher.code)
    else:
        q = Teacher.query
    if schedule:
        q = db_schedule.query_filter(q.join(Schedule))
    else:
        q = q.filter(Teacher.school == db_utils.school())
    if id_list:
        q = q.filter(Teacher.id.in_((id_list)))
    q = q.distinct().order_by(Teacher.code).all()
    if not full_name:
        return q
    return [(i, '{} ({} {})'.format(c, f, l)) for i, c, f, l in q]

def db_teacher(id=None, code=None, full_name=False):
    if id:
        teacher =  Teacher.query.get(id)
    elif code:
        teacher = Teacher.query.filter(Teacher.code == func.binary(code), Teacher.school == db_utils.school()).first()
    if not full_name:
        return teacher
    elif teacher:
        return '{} ({} {})'.format(teacher.code, teacher.first_name, teacher.last_name)
    return None