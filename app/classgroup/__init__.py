# -*- coding: utf-8 -*-

from flask import Blueprint

classgroup = Blueprint('classgroup', __name__)

from . import views