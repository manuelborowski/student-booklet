# -*- coding: utf-8 -*-
# app/home/__init__.py

from flask import Blueprint

reviewed = Blueprint('reviewed', __name__)

from . import views