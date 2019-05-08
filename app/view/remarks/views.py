from flask import render_template, url_for, request, redirect, jsonify
from flask_login import login_required

import app.database.db_utils
from . import remarks
from app import db, log
from app.database.models import Remark, RemarkSubject, RemarkMeasure, SubjectTopic, MeasureTopic, Student
from app.layout.forms import RemarkForm
from app.database.multiple_items import build_filter_and_filter_data, prepare_data_for_html
from app.utils import utils
from app.layout.tables_config import tables_configuration
from app.database.db_remark import db_filter_remarks_to_be_reviewed, db_add_extra_measure, db_tag_remarks_as_reviewed, check_if_duplicate

import json, datetime


@remarks.route('/remarks/data', methods=['GET', 'POST'])
@login_required
def data():
    ajax_table = prepare_data_for_html(tables_configuration['remark'])
    return ajax_table


@remarks.route('/remarks', methods=['GET', 'POST'])
@login_required
def show():
    # The following line is required only to build the filter-fields on the page.
    _filter, _filter_form, a, b, c = build_filter_and_filter_data(tables_configuration['remark'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config=tables_configuration['remark'])


@remarks.route('/remarks/action', methods=['GET', 'POST'])
@login_required
def action():
    try:
        if utils.button_pressed('delete'):
            chbx_id_list = request.form.getlist('chbx')
            for id in chbx_id_list:
                remark = Remark.query.get(int(id))
                if remark:
                    db.session.delete(remark)
            db.session.commit()
            return redirect(url_for('remarks.show'))
        if utils.button_pressed('edit'):
            chbx_id = request.form.getlist('chbx')[0]
            remark = db.session.query(Remark).join(Student).filter(Remark.id==chbx_id).first()
            form_remark = RemarkForm()

            remark.measure_topics = []
            for m in remark.measures:
                remark.measure_topics.append(m.topic.id)

            remark.subject_topics = []
            for m in remark.subjects:
                remark.subject_topics.append(m.topic.id)


            prime_data = {}
            h = remark.timestamp.second if 0 < remark.timestamp.second < 10 else 1
            prime_data['hour'] = h
            prime_data['date'] = remark.timestamp.strftime('%d-%m-%Y')
            prime_data['remark'] = remark


            return render_template('remark/remark.html', subject='remarks', action='edit',
                                   form=form_remark, students=[remark.student], prime_data=prime_data)
        if utils.button_pressed('start-review'):
            return start_review()

    except Exception as e:
        log.error('action {} gave error {}'.format(utils.button_pressed(), e))
        utils.flash_plus("Er is een fout opgetreden", e)
    return redirect(url_for('remarks.show'))


@remarks.route('/registrations/action_done/<string:action>/<int:id>', methods=['GET', 'POST'])
@remarks.route('/registrations/action_done/<string:action>', methods=['GET', 'POST'])
@login_required
def action_done(action=None, id=-1):
    if utils.button_pressed('save'):
        if action == 'edit':
            try:
                r_id = request.form['remark_id']
                remark = Remark.query.get(int(r_id))
                if remark:
                    measure_note = request.form['measure_note'] if request.form['measure_note'] != '' else None
                    subject_note = request.form['subject_note'] if request.form['subject_note'] != '' else None
                    extra_attention = 'chkb_extra_attention' in request.form
                    subjects = request.form.getlist('subject')
                    measures = request.form.getlist('measure')
                    timestamp = datetime.datetime.strptime('{} {}:{}:{}'.format(request.form['txt-date'], 23, 59, int(request.form['hour'])),
                                                           '%d-%m-%Y %H:%M:%S')
                    duplicate_remarks = False
                    if check_if_duplicate(remark.student, timestamp, measure_note, subject_note, extra_attention, measures, subjects):
                        duplicate_remarks = True
                        db.session.delete(remark)
                    else:
                        for t in RemarkSubject.query.filter(RemarkSubject.remark_id == remark.id).all(): db.session.delete(t)
                        for m in RemarkMeasure.query.filter(RemarkMeasure.remark_id == remark.id).all(): db.session.delete(m)
                        for t in subjects: db.session.add(RemarkSubject(topic=SubjectTopic.query.get(int(t)), remark=remark))
                        for m in measures: db.session.add(RemarkMeasure(topic=MeasureTopic.query.get(int(m)), remark=remark))
                        remark.measure_note = measure_note
                        remark.subject_note = subject_note
                        remark.extra_attention = extra_attention
                        remark.timestamp = timestamp
                    db.session.commit()
                    if duplicate_remarks:
                        utils.flash_plus('Er bestaat al een opmerking voor deze leerling(en) op dit tijdstip.<br>De opmerkingen worden samengevoegd')
                return redirect(url_for('remarks.show'))
            except Exception as e:
                log.error(u'Could not edit remarks {}'.format(e))
                utils.flash_plus(u'Kan opmerkingen niet aanpassen', e)

        if action == 'review-done':
            return review_done()

    return redirect(url_for('remarks.show'))


def start_review():
    try:
        academic_year = app.database.db_utils.academic_year()
        matched_remarks, non_matched_remarks = db_filter_remarks_to_be_reviewed(academic_year)
        for s, rll in matched_remarks:
            for id, extra_measure, rl in rll:
                for r in rl:
                    r.overwrite_row_color = r.row_color()
                    r.print_date = r.decode_timestamp()
                    r.print_subjects = r.ret_subjects()
                    r.print_measures = r.ret_measures()

    except Exception as e:
        log.error(u'Could not prepare the review : {}'.format(e))
        utils.flash_plus(u'Kan de controle niet voorbereiden', e)
        return redirect(url_for('remarks.show'))

    return render_template('remark/review.html',
                           matched_remarks=matched_remarks,
                           selected_academic_year=academic_year)


def review_done():
    try:
        db_tag_remarks_as_reviewed()
    except Exception as e:
        log.error(u'Could not set the remarks in reviewed state : {}'.format(e))
        utils.flash_plus('Kan de controle niet afronden', e)
    return redirect(url_for('reviewed.show'), code=307)


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
        return jsonify({'status': False})
    return jsonify({'status': True})


@remarks.route('/remarks/delete_extra_measure/<int:remark_id>', methods=['GET', 'POST'])
@login_required
def delete_extra_measure(remark_id):
    try:
        remark = Remark.query.get(remark_id)
        remarks = Remark.query.filter(Remark.extra_measure == remark.extra_measure).all()
        db.session.delete(remark.extra_measure)
        for r in remarks:
            r.first_remark = False
            r.extra_measure = None
        db.session.commit()
    except Exception as e:
        log.error(u'Could not delete extra measure : {}'.format(e))
        return jsonify({'status': False})
    return jsonify({'status': True})
