import app.database.db_utils
from app import db, log
from app.utils import utils
from app.database.models import  MeasureTopic


def db_measure_topic_list(select=False, all=False):
    school = app.database.db_utils.school()
    if select:
        q = db.session.query(MeasureTopic.id, MeasureTopic.topic)
    else:
        q = MeasureTopic.query
    if not all:
        q = q.filter(MeasureTopic.enabled == True)
    return q.filter(MeasureTopic.school == school).order_by(MeasureTopic.topic).all()


def add_default_values_if_empty():
    for school, topics in MeasureTopic.default_topics:
        find_topics = MeasureTopic.query.filter(school == school).all()
        if not find_topics:
            log.info('MeasureTopic table is empty, adding default values')
            for t in topics:
                db.session.add(MeasureTopic(topic=t, school=school))
    db.session.commit()
