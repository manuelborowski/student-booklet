import app.database.db_utils
from app.database.models import Student
from app.utils import utils

def db_student_list(grade=None):
    q = Student.query
    if grade:
        q = q.filter(Student.grade == grade)
    return q.filter(Student.academic_year == app.database.db_utils.academic_year()).order_by(Student.last_name, Student.first_name).all()
