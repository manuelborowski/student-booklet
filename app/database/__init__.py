from app import app
from app.database.models import Hub, SubjectTopic, MeasureTopic


@app.before_first_request
def at_start():
    Hub.add_default_values_if_empty()
    SubjectTopic.add_default_values_if_empty()
    MeasureTopic.add_default_values_if_empty()