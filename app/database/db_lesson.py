from app import db
from app.database.models import Lesson, Schedule, Teacher
from app.utils import utils


def db_lesson_list(teacher=None, select=False, academic_year=None):
    if select:
        q = db.session.query(Lesson.id, Lesson.code)
    else:
        q = Lesson.query
    q = q.join(Schedule)
    if teacher:
        q = q.join(Teacher).filter(Teacher.id == teacher.id)
    academic_year = academic_year if academic_year else utils.academic_year()
    q = q.filter(Schedule.school == utils.school(), Schedule.academic_year == academic_year)
    return q.distinct(Lesson.code).order_by(Lesson.code).all()

def db_lesson(id):
    return Lesson.query.get(id)
