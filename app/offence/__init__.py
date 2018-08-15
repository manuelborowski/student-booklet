# -*- coding: utf-8 -*-
# app/home/__init__.py

from flask import Blueprint

offence = Blueprint('offence', __name__)

from . import views