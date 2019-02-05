# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import SelectField

from ..models import Schedule, Lesson


class FilterForm(FlaskForm):
    teacher = SelectField('Leerkracht', choices=[])
    dayhour = SelectField('Dag en uur', choices=[])
    grade = SelectField('Klas', choices=[])
    lesson = SelectField('Vak', choices=[])

