# -*- coding: utf-8 -*-
#app/asset/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, DecimalField,  IntegerField, BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, ValidationError
from wtforms.widgets import HiddenInput
#from .. import _

from ..models import Teacher, Classgroup, Classmoment


class EditForm(FlaskForm):
    teacher = SelectField('Leerkracht', choices=zip(Teacher.get_list(), Teacher.get_list()))
    dayhour = SelectField('Dag en uur', choices=zip(Classmoment.get_day_hour(), Classmoment.get_day_hour()))
    classgroup = SelectField('Klas', choices=zip(Classgroup.get_list(), Classgroup.get_list()))
    id = IntegerField(widget=HiddenInput())


class AddForm(EditForm):
    pass

class ViewForm(FlaskForm):
    name = StringField('Naam', render_kw={'readonly':''})
    location = StringField('Locatie', render_kw={'readonly':''})
    qr_code = StringField('QR', render_kw={'readonly':''})
    status = StringField('Status', render_kw={'readonly':''})
    purchase = StringField('Aankoop', render_kw={'readonly':''})
    since = DateField('Datum', render_kw={'readonly':''}, format='%d-%m-%Y')
    value = DecimalField('Bedrag (&euro;)', render_kw={'readonly':''})
    supplier = StringField('Leverancier', render_kw={'readonly':''})
    category = StringField('Categorie', render_kw={'readonly':''})
    serial = StringField('SerieNr', render_kw={'readonly':''})

    brand = StringField('Merk', render_kw={'readonly':''})
    type = StringField('Type', render_kw={'readonly':''})
    power = DecimalField('Vermogen', render_kw={'readonly':''})
    ce = BooleanField('CE', render_kw={'readonly':''})
    risk_analysis = StringField('Risicoanalyse', render_kw={'readonly':''})
    manual = StringField('Handleiding', render_kw={'readonly':''})
    safety_information = StringField('VIK', render_kw={'readonly':''})
    photo = StringField('Foto', render_kw={'readonly':''})


    id = IntegerField(widget=HiddenInput())
