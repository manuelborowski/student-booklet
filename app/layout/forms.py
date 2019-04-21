from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField
from wtforms.widgets import HiddenInput

from  app.database import db_utils, db_lesson, db_grade, db_teacher
from app.database.models import Schedule
from app.utils import utils
from app.database import db_subject_topic, db_measure_topic, db_schedule

class SchoolyearFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(SchoolyearFilter, self).__init__(*args, **kwargs)
        sys = db_schedule.db_schedule_academic_year_list()
        sys = [''] + sys
        self.academic_year.choices = list(zip(sys, sys))

    academic_year = SelectField(default=db_utils.academic_year(), label='Schooljaar')
    default_academic_year = db_utils.academic_year()


class GradeFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(GradeFilter, self).__init__(*args, **kwargs)
        self.grade.choices = [('', '')] + db_grade.db_grade_list(select=True)

    grade = SelectField(default='', label='Klas')


class TeacherFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(TeacherFilter, self).__init__(*args, **kwargs)
        self.teacher.choices = [('', '')] + db_teacher.db_teacher_list(full_name=True, schedule=False, select=True)

    teacher = SelectField(default='', label='leerkracht')


class RemarkForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(RemarkForm, self).__init__(*args, **kwargs)
        self.subject.choices = db_subject_topic.db_subject_topic_list(select=True)
        self.measure.choices = db_measure_topic.db_measure_topic_list(select=True)

    subject = SelectField('Opmerking')
    measure = SelectField('Maatregel')
    id = IntegerField(widget=HiddenInput())
