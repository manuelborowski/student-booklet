from app import log, db
from app.database.models import ReplacementTeacher

def replacement_list(id=None, ids_only=False):
    if id:
        if ids_only:
            q = db.session.query(ReplacementTeacher.replacing_id)
        else:
            q = db.session.query(ReplacementTeacher)
        q = q.filter(ReplacementTeacher.replaced_by_id == id).all()
        if ids_only:
            return [k for k, in q]
        else:
            return q
    return []