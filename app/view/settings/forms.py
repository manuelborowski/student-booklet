# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, ValidationError, IntegerField, SelectField
from wtforms.validators import DataRequired
from wtforms.widgets import HiddenInput
from sqlalchemy import func
from app.database import db_teacher

from app.database.models import User


class EditReplacementForm(FlaskForm):
    replaced_by = SelectField('Vervangende leerkracht', choices=db_teacher.db_teacher_list(select=True, schedule=False))
    id = IntegerField(widget=HiddenInput())

class AddReplacementForm(EditReplacementForm):
    pass

