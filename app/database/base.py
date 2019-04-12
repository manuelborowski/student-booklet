from app.database.models import Hub, SubjectTopic, MeasureTopic, Grade, Lesson


def db_get_school():
    return Hub.SCHOOL.LYCEUM




def db_get_hub(school=None, academic_year=None, valid_from=None, test=False):
    if not school:
        school=db_get_school()
    return Hub.get_hub(school, academic_year, valid_from, test)

def db_hub_get_all_academic_years():
    return Hub.get_all_academic_years_from_database()



def db_grade_get_grades():
    hub=db_get_hub()
    return Grade.query.filter(hub==hub).all()


def db_subject_topic_get_list():
    hub=db_get_hub()
    return SubjectTopic.query.filter(hub==hub).all()


def db_measure_topic_get_list():
    hub=db_get_hub()
    return MeasureTopic.query.filter(hub==hub).all()