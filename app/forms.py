# -*- coding: utf-8 -*-
#app/forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField
from wtforms.widgets import HiddenInput
from models import Classgroup, Teacher, Type, Measure


class ClassgroupFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(ClassgroupFilter, self).__init__(*args, **kwargs)
        self.classgroup.choices=Classgroup.get_choices_with_empty_list()

    classgroup = SelectField('')

class TeacherFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(TeacherFilter, self).__init__(*args, **kwargs)
        self.teacher.choices=Teacher.get_choices_with_empty_list()

    teacher = SelectField('')

class OffenceForm(FlaskForm):
    type = SelectField('Overtreding', choices=Type.get_choices_list())
    measure = SelectField('Maatregel', choices=Measure.get_choices_list())
    id = IntegerField(widget=HiddenInput())