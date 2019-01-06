# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import SelectField

from ..models import Teacher, Classgroup, Classmoment, Lesson


class ViewForm(FlaskForm):
    teacher = SelectField('Leerkracht', choices=Teacher.get_choices_list())
    dayhour = SelectField('Dag en uur', choices=Classmoment.get_choices_day_hour())
    classgroup = SelectField('Klas', choices=Classgroup.get_choices_list())
    lesson = SelectField('Vak', choices=Lesson.get_choices_list())


