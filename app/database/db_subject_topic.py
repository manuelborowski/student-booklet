from app import db, log
from app.utils import utils
from app.database.models import SubjectTopic


def db_subject_topic_list(select=False, all=False):
    school = utils.school()
    if select:
        q = db.session.query(SubjectTopic.id, SubjectTopic.topic)
    else:
        q = SubjectTopic.query
    if not all:
        q = q.filter(SubjectTopic.enabled == True)
    return q.filter(SubjectTopic.school == school).order_by(SubjectTopic.topic).all()

def add_default_values_if_empty():
    for school, topics in SubjectTopic.default_topics:
        find_topics = SubjectTopic.query.filter(school==school).all()
        if not find_topics:
            log.info('SubjectTopic table is empty, adding default values')
            for t in topics:
                db.session.add(SubjectTopic(topic=t, school=school))
    db.session.commit()
