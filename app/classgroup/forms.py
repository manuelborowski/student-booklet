# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, DecimalField,  IntegerField, BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, ValidationError
#from .. import _

from ..models import Teacher, Classgroup, Classmoment, Offence, Type, Measure, Lesson


class ViewForm(FlaskForm):
    teacher = SelectField('Leerkracht', choices=Teacher.get_choices_list())
    dayhour = SelectField('Dag en uur', choices=Classmoment.get_choices_day_hour())
    classgroup = SelectField('Klas', choices=Classgroup.get_choices_list())
    lesson = SelectField('Vak', choices=Lesson.get_choices_list())


