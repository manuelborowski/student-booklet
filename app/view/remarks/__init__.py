# -*- coding: utf-8 -*-
# app/home/__init__.py

from flask import Blueprint

remarks = Blueprint('remarks', __name__)

from . import views