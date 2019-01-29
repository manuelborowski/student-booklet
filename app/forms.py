# -*- coding: utf-8 -*-
#app/forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField
from wtforms.widgets import HiddenInput
from models import Classgroup, Teacher, Type, Measure
from .base import get_all_schoolyears_from_database, calculate_current_schoolyear


class SchoolyearFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(SchoolyearFilter, self).__init__(*args, **kwargs)
        sys = get_all_schoolyears_from_database()
        sys = [''] + sys
        self.schoolyear.choices=zip(sys, sys)

    schoolyear = SelectField(default=calculate_current_schoolyear(), label='Schooljaar')
    default_schoolyear = calculate_current_schoolyear()

class ClassgroupFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(ClassgroupFilter, self).__init__(*args, **kwargs)
        self.classgroup.choices=Classgroup.get_choices_with_empty_list()
    classgroup = SelectField(default='', label='Klas')

class TeacherFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(TeacherFilter, self).__init__(*args, **kwargs)
        self.teacher.choices=Teacher.get_choices_with_empty_list()
    teacher = SelectField(default='', label='leerkracht')

class OffenceForm(FlaskForm):
    type = SelectField('Overtreding', choices=Type.get_choices_list())
    measure = SelectField('Maatregel', choices=Measure.get_choices_list())
    id = IntegerField(widget=HiddenInput())