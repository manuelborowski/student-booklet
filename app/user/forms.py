# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, ValidationError, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.widgets import HiddenInput
from sqlalchemy import func

from ..models import User


class EditForm(FlaskForm):
    first_name = StringField('First name')
    last_name = StringField('Last name')
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    level = SelectField('Niveau', validators=[DataRequired()], choices=User.get_zipped_levels())
    type = SelectField('Type', validators=[DataRequired()], choices=User.get_zipped_types())
    id = IntegerField(widget=HiddenInput())

class AddForm(EditForm):
    #password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm_password')])
    #confirm_password = PasswordField('Confirm Password')
    password = PasswordField('Password')
    confirm_password = PasswordField('Bevestig Password')
    def validate_username(self, field):
        if User.query.filter_by(username=func.binary(field.data)).first():
            raise ValidationError('Gebruikersnaam is reeds in gebruik')

    def validate_password(self, field):
        if self.type.data == User.USER_TYPE.LOCAL and field.data == '':
            raise ValidationError('Paswoord invullen aub')

    def validate_confirm_password(self, field):
        if self.type.data == User.USER_TYPE.LOCAL and field.data != self.password.data:
            raise ValidationError('Beide paswoorden moeten hetzelfde zijn')

    # def validate(self):
    #     print('validating')
    #     if self.type.data == User.USER_TYPE.LOCAL:
    #         if self.password.data == '':
    #             raise ValidationError('Paswoord invullen aub')
    #             self.password.errors.append('Paswoord invullen aub')
    #             return False
    #     if self.confirm_password.data != self.password.data:
    #         self.config_password.errors.append('De twee paswoorden moeten gelijk zijn')
    #         return False
    #     return True

class ViewForm(FlaskForm):
    first_name = StringField('First name', render_kw={'readonly':''})
    last_name = StringField('Last name', render_kw={'readonly':''})
    username = StringField('Username', render_kw={'readonly':''})
    email = StringField('Email', render_kw={'readonly':''})
    level = StringField('Niveau', render_kw={'readonly':''}, filters=[lambda i : User.LEVEL.i2s(i)])
    type = StringField('Type', render_kw={'readonly':''})
    id = IntegerField(widget=HiddenInput())

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), EqualTo('confirm_new_password')])
    confirm_new_password = PasswordField('Confirm new password')
