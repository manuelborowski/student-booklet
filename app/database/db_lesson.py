from app import db
from  app.database import db_utils
from app.database.models import Lesson, Schedule, Teacher


def db_lesson_list(teacher=None, select=False):
    if select:
        q = db.session.query(Lesson.id, Lesson.code)
    else:
        q = Lesson.query
    if teacher:
        academic_year = db_utils.academic_year()
        q = q.join(Schedule, Teacher).filter(Teacher.id == teacher.id, Schedule.school == db_utils.school(), Schedule.academic_year == academic_year)
    else:
        q = q.filter(Lesson.school == db_utils.school())
    return q.distinct(Lesson.code).order_by(Lesson.code).all()

def db_lesson(id):
    return Lesson.query.get(id)
