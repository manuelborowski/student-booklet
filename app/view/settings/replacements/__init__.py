# -*- coding: utf-8 -*-
# app/home/__init__.py

from flask import Blueprint

replacements = Blueprint('settings.replacements', __name__)

from . import views