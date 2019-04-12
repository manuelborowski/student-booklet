# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import SelectField


class FilterForm(FlaskForm):
    teacher = SelectField('Leerkracht', choices=[])
    dayhour = SelectField('Lesuur', choices=[])
    grade = SelectField('Klas', choices=[])
    lesson = SelectField('Vak', choices=[])

