# -*- coding: utf-8 -*-

from flask import render_template
from flask_login import login_required

from . import reviewed
from ..base_multiple_items import build_filter_and_filter_data, prepare_data_for_html
from ..tables_config import  tables_configuration

@reviewed.route('/reviewed/data', methods=['GET', 'POST'])
@login_required
def source_data():
    ajax_table =  prepare_data_for_html(tables_configuration['extra_measure'])
    return ajax_table


@reviewed.route('/reviewed/show', methods=['GET', 'POST'])
@login_required
def show():
    _filter, _filter_form, a,b, c = build_filter_and_filter_data(tables_configuration['extra_measure'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['extra_measure'])
