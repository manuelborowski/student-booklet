from app import db
from  app.database import db_utils, db_schedule
from app.database.models import Lesson, Schedule, Teacher


def db_lesson_list(teacher=None, select=False, schedule=True):
    if select:
        q = db.session.query(Lesson.id, Lesson.code)
    else:
        q = Lesson.query
    if teacher:
        q = db_schedule.query_filter(q.join(Schedule, Teacher)).filter(Teacher.id == teacher.id)
    else:
        if schedule:
            q = db_schedule.query_filter(q.join(Schedule))
        else:
            q = q.join(Schedule).filter(Schedule.school == db_utils.school())
    return q.distinct(Lesson.code).order_by(Lesson.code).all()

def db_lesson(id):
    return Lesson.query.get(id)
