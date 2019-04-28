from app.database import db_utils
from app.database.models import Student
from app.utils import utils

def db_student_list(classgroup=None):
    q = Student.query
    if classgroup:
        q = q.filter(Student.classgroup == classgroup)
    return q.filter(Student.academic_year == db_utils.academic_year()).order_by(Student.last_name, Student.first_name).all()
