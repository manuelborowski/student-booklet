from app import log, db
from app.database.models import ReplacementTeacher, Teacher
from sqlalchemy import or_

def replacement_list(id=None, absent_teachers=False):
    if id:
        if absent_teachers:
            q = db.session.query(ReplacementTeacher.replacing_id)
        else:
            q = db.session.query(ReplacementTeacher)
        return q.filter(ReplacementTeacher.replaced_by_id == id).all()
    return []