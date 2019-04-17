from app import log, db
from app.database.models import ReplacementTeacher, Teacher
from sqlalchemy import or_

def replacement_list():
    try:
        replacements = db.session.query(ReplacementTeacher, Teacher).join(Teacher, or_(ReplacementTeacher.replacing_id == Teacher.id,
                                                                                       ReplacementTeacher.replaced_by_id == Teacher.id)).all()
        return replacements
    except Exception as e:
        log.error('Could not get the replacement teachers error {}'.format(e))
        return []
    return []
