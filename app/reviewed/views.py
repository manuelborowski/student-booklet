# -*- coding: utf-8 -*-

from flask import render_template, jsonify
from flask_login import login_required
import json
from . import reviewed
from ..base_multiple_items import build_filter_and_filter_data, prepare_data_for_html
from ..tables_config import  tables_configuration
from .. import log, db
from .. models import Remark, Student, Teacher, RemarkSubject, RemarkMeasure

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

@reviewed.route('/reviewed/get_row_detail/<string:data>', methods=['GET', 'POST'])
@login_required
def get_row_detail(data):
    try:
        jd = json.loads(data)
        remarks = Remark.query.join(Student, Teacher, RemarkSubject, RemarkMeasure).filter(Remark.extra_measure_id==jd['id'])
        details = [r.ret_dict() for r in remarks]
        return jsonify({"status": True, "details" : details})
    except Exception as e:
        log.error('could not change the status')
        return jsonify({"status" : False})

    return jsonify({"status" : False})
