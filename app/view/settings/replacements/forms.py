# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField
from wtforms.widgets import HiddenInput
from app.database import db_teacher



class EditForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)
        self.replaced_by.choices=db_teacher.db_teacher_list(select=True, schedule=False, full_name=True)

    replaced_by = SelectField('Vervangende leerkracht')
    id = IntegerField(widget=HiddenInput())

class AddForm(EditForm):
    pass
