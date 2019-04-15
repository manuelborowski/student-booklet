from app import app
from . import db_measure_topic, db_subject_topic


@app.before_first_request
def at_start():
    db_subject_topic.add_default_values_if_empty()
    db_measure_topic.add_default_values_if_empty()