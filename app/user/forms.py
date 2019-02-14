# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, ValidationError, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.widgets import HiddenInput
from sqlalchemy import func

from ..models import User


class EditForm(FlaskForm):
    first_name = StringField('Voornaam')
    last_name = StringField('Achternaam')
    username = StringField('Gebruikersnaam', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    level = SelectField('Niveau', validators=[DataRequired()], choices=User.get_zipped_levels())
    user_type = SelectField('Type', validators=[DataRequired()], choices=User.get_zipped_types())
    id = IntegerField(widget=HiddenInput())

class AddForm(EditForm):
    password = PasswordField('Paswoord')
    confirm_password = PasswordField('Bevestig Paswoord')
    def validate_username(self, field):
        if User.query.filter_by(username=func.binary(field.data)).first():
            raise ValidationError('Gebruikersnaam is reeds in gebruik')

    def validate_password(self, field):
        if self.user_type.data == User.USER_TYPE.LOCAL and field.data == '':
            raise ValidationError('Paswoord invullen aub')

    def validate_confirm_password(self, field):
        if self.user_type.data == User.USER_TYPE.LOCAL and field.data != self.password.data:
            raise ValidationError('Beide paswoorden moeten hetzelfde zijn')

class ViewForm(FlaskForm):
    first_name = StringField('First name', render_kw={'readonly':''})
    last_name = StringField('Last name', render_kw={'readonly':''})
    username = StringField('Username', render_kw={'readonly':''})
    email = StringField('Email', render_kw={'readonly':''})
    level = StringField('Niveau', render_kw={'readonly':''}, filters=[lambda i : User.LEVEL.i2s(i)])
    user_type = StringField('Type', render_kw={'readonly':''})
    id = IntegerField(widget=HiddenInput())

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Oud paswoord')
    new_password = PasswordField('Nieuw Paswoord')
    confirm_new_password = PasswordField('Bevestig nieuw paswoord')
    id = IntegerField(widget=HiddenInput())

    def validate_old_password(self, field):
        user = User.query.get(self.id.data)
        if not user or not user.verify_password(field.data):
            raise ValidationError('Verkeerd paswoord opgegeven')

    def validate_new_password(self, field):
        if field.data == '':
            raise ValidationError('Paswoord invullen aub')

    def validate_confirm_new_password(self, field):
        if field.data != self.new_password.data:
            raise ValidationError('Beide paswoorden moeten hetzelfde zijn')