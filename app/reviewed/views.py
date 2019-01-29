# -*- coding: utf-8 -*-

from flask import render_template, url_for, request, flash, redirect, jsonify
from flask_login import login_required, current_user

from .. import db, log, app
from . import reviewed
from ..models import Offence, Type, Measure, Student, ExtraMeasure
from ..forms import OffenceForm
from ..base_multiple_items import build_filter_and_filter_data, prepare_data_for_html
from ..tables_config import  tables_configuration

import datetime, json, base64

@reviewed.route('/reviewed/data', methods=['GET', 'POST'])
@login_required
def source_data():
    only_checkbox_for = current_user.username if current_user.is_strict_user else None
    start = datetime.datetime.now()
    ajax_table =  prepare_data_for_html(tables_configuration['extra_measure'])
    stop = datetime.datetime.now()
    print('ajax data call {}'.format(stop-start))
    return ajax_table


@reviewed.route('/reviewed/show', methods=['GET', 'POST'])
@login_required
def show():
    _filter, _filter_form, a,b, c = build_filter_and_filter_data(tables_configuration['extra_measure'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['extra_measure'])
