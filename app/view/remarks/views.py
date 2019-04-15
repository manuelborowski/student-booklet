from flask import render_template, url_for, request, redirect, jsonify
from flask_login import login_required

from . import remarks
from app import db, log
from app.database.models import Remark, RemarkSubject, RemarkMeasure, SubjectTopic, MeasureTopic
from app.layout.forms import RemarkForm
from app.database.multiple_items import build_filter_and_filter_data, prepare_data_for_html
from app.utils import utils
from app.layout.tables_config import  tables_configuration
from app.database.db_remark import db_filter_remarks_to_be_reviewed, db_add_extra_measure, db_tag_remarks_as_reviewed

import json

@remarks.route('/remarks/data', methods=['GET', 'POST'])
@login_required
def source_data():
    ajax_table =  prepare_data_for_html(tables_configuration['remark'])
    return ajax_table

@remarks.route('/remarks', methods=['GET', 'POST'])
@login_required
def show():
    #The following line is required only to build the filter-fields on the page.
    _filter, _filter_form, a,b, c = build_filter_and_filter_data(tables_configuration['remark'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['remark'])

@remarks.route('/remarks/delete', methods=['GET', 'POST'])
@login_required
def delete():
    try:
        cb_id_list = request.form.getlist('cb')
        for id in cb_id_list:
            remark = Remark.query.get(int(id))
            if remark:
                db.session.delete(remark)
                if remark.extra_measure:
                    db.session.delete(remark.extra_measure)
        db.session.commit()
        return redirect(url_for('remarks.show'))
    except Exception as e:
        log.error(u'Could not delete remark : {}'.format(e))
        utils.flash_plus('Kan de opmerkingen niet verwijderen', e)
    _filter, _filter_form, a,b, c = build_filter_and_filter_data(tables_configuration['remark'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['remark'])

@remarks.route('/remarks/edit', methods=['GET', 'POST'])
@login_required
def edit():
    try:
        if utils.button_save_pushed(): #second pass
            # iterate over the remarks, delete the old subjects and measures and attach the new
            for r in request.form.getlist('remark_id'):
                remark = Remark.query.get(int(r))
                if remark:
                    for t in RemarkSubject.query.filter(RemarkSubject.remark_id == remark.id).all(): db.session.delete(t)
                    for m in RemarkMeasure.query.filter(RemarkMeasure.remark_id == remark.id).all(): db.session.delete(m)
                    for t in request.form.getlist('subject'): db.session.add(RemarkSubject(topic=SubjectTopic.query.get(int(t)), remark=remark))
                    for m in request.form.getlist('measure'): db.session.add(RemarkMeasure(topic=MeasureTopic.query.get(int(m)), remark=remark))
                    remark.measure_note = request.form['measure_note']
                    remark.subject_note = request.form['subject_note']
                    remark.extra_attention='chkb_extra_attention' in request.form
            db.session.commit()
            return redirect(url_for('remarks.show'))
        else:  # first pass
            students = set()
            remarks = []
            cb_id_list = request.form.getlist('cb')
            for id in cb_id_list:
                remark = Remark.query.get(int(id))
                if remark:
                    remarks.append(remark)
                    students.add(remark.student)
            form_remark = RemarkForm()
            return render_template('remark/remark.html',
                                   subject = 'remarks',
                                   role = 'edit',
                                   save_filters=None,
                                   save_remarks=remarks,
                                   form_remark=form_remark,
                                   students=students)
    except Exception as e:
        log.error(u'Could not edit remarks {}'.format(e))
        utils.flash_plus(u'Kan opmerkingen niet aanpassen', e)
    return redirect(url_for('remarks.show'))


@remarks.route('/remarks/start_review', methods=['GET', 'POST'])
@login_required
def start_review():
    try:
        academic_year = utils.academic_year() if request.form['academic_year'] == '' else request.form['academic_year']
        matched_remarks, non_matched_remarks = db_filter_remarks_to_be_reviewed(academic_year)
        for s, rll in matched_remarks:
            for id, extra_measure, rl in rll:
                for r in rl:
                    r.overwrite_row_color = r.row_color()
                    r.print_date = r.timestamp.strftime('%d-%m-%Y %H:%M')
                    r.print_subjects = r.ret_subjects()
                    r.print_measures = r.ret_measures()

        for r in non_matched_remarks:
            r.print_date = r.timestamp.strftime('%d-%m-%Y %H:%M')
            r.print_subjects = r.ret_subjects()
            r.print_measures = r.ret_measures()

    except Exception as e:
        log.error(u'Could not prepare the review : {}'.format(e))
        utils.flash_plus(u'Kan de controle niet voorbereiden', e)
        return redirect(url_for('remarks.show'))

    return render_template('remark/review.html',
                        matched_remarks=matched_remarks,
                        non_matched_remarks=non_matched_remarks,
                        selected_academic_year=academic_year)


@remarks.route('/remarks/add_extra_measure/<string:remark_ids>/<string:em>', methods=['GET', 'POST'])
@login_required
def add_extra_measure(remark_ids, em):
    try:
        rids = json.loads(remark_ids)
        rid_list = [int(i) for i in rids]
        em = em.replace('&47;', '/')
        db_add_extra_measure(rid_list, em)
    except Exception as e:
        log.error(u'Could not add extra measure : {}'.format(e))
        return jsonify({'status' : False})
    return jsonify({'status' : True})

@remarks.route('/remarks/delete_extra_measure/<int:remark_id>', methods=['GET', 'POST'])
@login_required
def delete_extra_measure(remark_id):
    try:
        remark = Remark.query.get(remark_id)
        remarks = Remark.query.filter(Remark.extra_measure==remark.extra_measure).all()
        db.session.delete(remark.extra_measure)
        for r in remarks:
            r.first_remark = False
            r.extra_measure = None
        db.session.commit()
    except Exception as e:
        log.error(u'Could not delete extra measure : {}'.format(e))
        return jsonify({'status' : False})
    return jsonify({'status' : True})

@remarks.route('/remarks/review_done', methods=['GET', 'POST'])
@login_required
def review_done():
    try:
        db_tag_remarks_as_reviewed()
    except Exception as e:
         log.error(u'Could not set the remarks in reviewed state : {}'.format(e))

    return redirect(url_for('reviewed.show'), code=307)
