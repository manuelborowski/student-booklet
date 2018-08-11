# -*- coding: utf-8 -*-
#app/asset/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, DecimalField,  IntegerField, BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, ValidationError
from wtforms.widgets import HiddenInput
#from .. import _

from ..models import Teacher, Classgroup, Classmoment, Offence, Type, Measure, Lesson


class ViewForm(FlaskForm):
    teacher = SelectField('Leerkracht', choices=Teacher.get_choices_list())
    dayhour = SelectField('Dag en uur', choices=Classmoment.get_choices_day_hour())
    classgroup = SelectField('Klas', choices=Classgroup.get_choices_list())
    lesson = SelectField('Vak', choices=Lesson.get_choices_list())


class OffenceForm(FlaskForm):
    type = SelectField('Overtreding', choices=Type.get_choices_list())
    measure = SelectField('Maatregel', choices=Measure.get_choices_list())
    id = IntegerField(widget=HiddenInput())
