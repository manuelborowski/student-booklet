# -*- coding: utf-8 -*-
#app/forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField
from wtforms.widgets import HiddenInput
from models import Grade, Teacher, RemarkSubject, RemarkMeasure
from .base import get_all_schoolyears_from_database, calculate_current_schoolyear


class SchoolyearFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(SchoolyearFilter, self).__init__(*args, **kwargs)
        sys = get_all_schoolyears_from_database()
        sys = [''] + sys
        self.schoolyear.choices=zip(sys, sys)

    schoolyear = SelectField(default=calculate_current_schoolyear(), label='Schooljaar')
    default_schoolyear = calculate_current_schoolyear()

class GradeFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(GradeFilter, self).__init__(*args, **kwargs)
        self.grade.choices=Grade.get_choices_with_empty_list()
    grade = SelectField(default='', label='Klas')

class TeacherFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(TeacherFilter, self).__init__(*args, **kwargs)
        self.teacher.choices=Teacher.get_choices_with_empty_list()
    teacher = SelectField(default='', label='leerkracht')

class RemarkForm(FlaskForm):
    subject = SelectField('Opmerking', choices=RemarkSubject.get_choices_list())
    measure = SelectField('Maatregel', choices=RemarkMeasure.get_choices_list())
    id = IntegerField(widget=HiddenInput())