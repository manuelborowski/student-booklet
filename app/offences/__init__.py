# -*- coding: utf-8 -*-
# app/home/__init__.py

from flask import Blueprint

offences = Blueprint('offences', __name__)

from . import views