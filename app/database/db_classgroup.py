from app import db
from app.database import db_utils
from app.database.models import Grade, Classgroup


def db_classgroup_list(grade=None):
    q = Classgroup.query.join(Grade).filter(Grade.school == db_utils.school())
    if grade:
        q = q.filter(Classgroup.grade == grade)
    q = q.all()
    return q


def db_classgroup_dict():
    q = db.session.query(Classgroup, Grade).join(Grade).filter(Grade.school == db_utils.school()).all()
    d = {'{} {}'.format(i.Grade.code, i.ClassGroup.code): i.ClassGroup for i in q}
    return d
