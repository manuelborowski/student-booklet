# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, ValidationError, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.widgets import HiddenInput
from sqlalchemy import func

from app.database.models import User


class EditForm(FlaskForm):
    first_name = StringField('Voornaam')
    last_name = StringField('Achternaam')
    username = StringField('Gebruikersnaam', validators=[DataRequired()])
    email = StringField('Email')
    level = SelectField('Niveau', validators=[DataRequired()], choices=User.get_zipped_levels())
    user_type = SelectField('Type', validators=[DataRequired()], choices=User.get_zipped_types())
    id = IntegerField(widget=HiddenInput())

    change_password=SelectField('Paswoord aanpassen', choices=[('False', 'Neen'), ('True', 'Ja')])
    password = PasswordField('Paswoord')
    confirm_password = PasswordField('Bevestig Paswoord')

    def validate_password(self, field):
        if self.user_type.data == User.USER_TYPE.LOCAL:
            if self.change_password.data == 'True':
                if field.data == '':
                    raise ValidationError('Paswoord invullen aub')
            else:
                field.data = None
        else:
            field.data = None

    def validate_confirm_password(self, field):
        if self.user_type.data == User.USER_TYPE.LOCAL and self.password.data:
            if field.data != self.password.data:
                raise ValidationError('Beide paswoorden moeten hetzelfde zijn')
        else:
            field.data = None

    def validate_username(self, field):
        user = User.query.filter(User.username==func.binary(field.data)).first()
        if user and (not self.id.data or self.id.data and self.id.data != user.id):
            raise ValidationError('Gebruikersnaam is reeds in gebruik')


class AddForm(EditForm):
    pass
