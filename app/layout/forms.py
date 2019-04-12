# -*- coding: utf-8 -*-
#app/forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField
from wtforms.widgets import HiddenInput
from app.database.models import Schedule, MeasureTopic, SubjectTopic, Hub
from app.utils.base import get_academic_year


class SchoolyearFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(SchoolyearFilter, self).__init__(*args, **kwargs)
        sys = Hub.get_all_academic_years_from_database()
        sys = [''] + sys
        self.academic_year.choices=list(zip(sys, sys))

    academic_year = SelectField(default=get_academic_year(), label='Schooljaar')
    default_academic_year = get_academic_year()

class GradeFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(GradeFilter, self).__init__(*args, **kwargs)
        self.grade.choices=[('','')] + Schedule.get_all_grades()
    grade = SelectField(default='', label='Klas')

class TeacherFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(TeacherFilter, self).__init__(*args, **kwargs)
        self.teacher.choices=[('','')] + Schedule.get_all_teachers()
    teacher = SelectField(default='', label='leerkracht')

class RemarkForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(RemarkForm, self).__init__(*args, **kwargs)
        self.subject.choices=SubjectTopic.get_choices_list()
        self.measure.choices=MeasureTopic.get_choices_list()
    subject = SelectField('Opmerking')
    measure = SelectField('Maatregel')
    id = IntegerField(widget=HiddenInput())