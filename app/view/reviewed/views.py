# -*- coding: utf-8 -*-

from flask import render_template, jsonify
from flask_login import login_required
import json
from . import reviewed
from app.database.multiple_items import build_filter_and_filter_data, prepare_data_for_html
from app.layout.tables_config import  tables_configuration
from app import log, db
from app.database.models import Remark, Student, Teacher, Grade, Lesson

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
        remarks = db.session.query(Remark, Student, Grade, Teacher, Lesson).join(Student, Grade, Teacher, Lesson). \
            filter(Remark.extra_measure_id==jd['id']).all()
        details = Remark.format_data(remarks)
        return jsonify({"status": True, "details" : details})
    except Exception as e:
        log.error('could not change the status')
        return jsonify({"status" : False})

    return jsonify({"status" : False})
