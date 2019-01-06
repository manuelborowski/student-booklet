# -*- coding: utf-8 -*-
# app/asset/views.py

from flask import render_template, redirect, url_for, request, flash, send_file, session
from flask_login import login_required, current_user

#from .forms import AddForm, EditForm, ViewForm
from .. import db, log, app, admin_required
from . import offence
from ..models import Offence, Type, Measure, Teacher, Classgroup, Lesson
from ..forms import OffenceForm
from ..base import build_filter, get_ajax_table, get_global_setting_current_schoolyear
from ..tables_config import  tables_configuration
from ..documents import download_single_doc

import cStringIO, csv, re

from werkzeug.datastructures import FileStorage

@app.context_processor
def inject_schoolyear():
    return dict(schoolyear=get_global_setting_current_schoolyear())

@offence.route('/offence/data', methods=['GET', 'POST'])
@login_required
def source_data():
    return get_ajax_table(tables_configuration['offence'])

@offence.route('/offence', methods=['GET', 'POST'])
@login_required
def offences():
    if 'button' in request.form and request.form['button'] == 'Bewaar':
        try:
            #iterate over the offences, delete the old types and measures and attach the new
            for o in request.form.getlist('offence_id'):
                offence = Offence.query.get(int(o))
                if offence:
                    for t in Type.query.filter(Type.offence_id==offence.id).all(): db.session.delete(t)
                    for m in Measure.query.filter(Measure.offence_id==offence.id).all(): db.session.delete(m)
                    for t in request.form.getlist('type'): db.session.add(Type(type=int(t), offence=offence))
                    for m in request.form.getlist('measure'): db.session.add(Measure(measure=int(m), offence=offence))
                    offence.measure_note = request.form['comment_measure']
                    offence.type_note = request.form['comment_offence']

            db.session.commit()
        except Exception as e:
            log.error("Could not edit offences {}".format(e))
            flash('Kan opmerkingen niet aanpassen')
    #The following line is required only to build the filter-fields on the page.
    _filter, _filter_form, a,b, c = build_filter(tables_configuration['offence'])
    return render_template('base_multiple_items.html',
                           title='Opmerkingen',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['offence'])

@offence.route('/offence/delete', methods=['GET', 'POST'])
@login_required
@admin_required
def delete():
    try:
        cb_id_list = request.form.getlist('cb')
        for id in cb_id_list:
            offence = Offence.query.get(int(id))
            if offence: db.session.delete(offence)
        db.session.commit()
    except Exception as e:
        log.error('Could not delete offence : {}'.format(e))
        flash('Kan de opmerkingen niet verwijderen')

    #The following line is required only to build the filter-fields on the page.
    _filter, _filter_form, a,b, c = build_filter(tables_configuration['offence'])
    return render_template('base_multiple_items.html',
                           title='Opmerkingen',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['offence'])

@offence.route('/offence/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit():
    students = []
    offences = []
    try:
        cb_id_list = request.form.getlist('cb')
        for id in cb_id_list:
            offence = Offence.query.get(int(id))
            if offence:
                offences.append(offence)
                students.append(offence.student)
    except Exception as e:
        log.error('Could not edit offences : {}'.format(e))
        flash('Kan de opmerkingen niet aanpassen')

    form_offence = OffenceForm()
    return render_template('offence/offence.html',
                           redirect_url = url_for('offence.offences'),
                           save_filters=None,
                           save_offences=offences,
                           form_offence=form_offence,
                           students=students)

