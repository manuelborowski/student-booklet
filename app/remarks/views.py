# -*- coding: utf-8 -*-

from flask import render_template, url_for, request, redirect, jsonify
from flask_login import login_required, current_user

from .. import db, log, app
from . import remarks
from ..models import Remark, RemarkSubject, RemarkMeasure, Student, ExtraMeasure, SubjectTopic, MeasureTopic
from ..forms import RemarkForm
from ..base_multiple_items import build_filter_and_filter_data, prepare_data_for_html
from ..base import calculate_current_schoolyear, flash_plus, button_save_pushed
from ..tables_config import  tables_configuration

import datetime, json

#This will make the variable 'schoolyear' default available in all templates
@app.context_processor
def inject_schoolyear():
    return dict(schoolyear=calculate_current_schoolyear())


@app.context_processor
def inject_url_rule():
    return dict(url_rule=request.url_rule)

@remarks.route('/remarks/data', methods=['GET', 'POST'])
@login_required
def source_data():
    only_checkbox_for = current_user.username if current_user.is_strict_user else None
    ajax_table =  prepare_data_for_html(tables_configuration['remark'], only_checkbox_for=only_checkbox_for)
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
        flash_plus('Kan de opmerkingen niet verwijderen', e)
    _filter, _filter_form, a,b, c = build_filter_and_filter_data(tables_configuration['remark'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['remark'])

@remarks.route('/remarks/edit', methods=['GET', 'POST'])
@login_required
def edit():
    try:
        if button_save_pushed(): #second pass
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
        flash_plus(u'Kan opmerkingen niet aanpassen', e)
    return redirect(url_for('remarks.show'))

    # if 'button' in request.form and request.form['button'] == 'Bewaar':
    #     try:
    #         #iterate over the remarks, delete the old subjects and measures and attach the new
    #         for r in request.form.getlist('remark_id'):
    #             remark = Remark.query.get(int(r))
    #             if remark:
    #                 for t in RemarkSubject.query.filter(RemarkSubject.remark_id == remark.id).all(): db.session.delete(t)
    #                 for m in RemarkMeasure.query.filter(RemarkMeasure.remark_id == remark.id).all(): db.session.delete(m)
    #                 for t in request.form.getlist('subject'): db.session.add(RemarkSubject(topic=SubjectTopic.query.get(int(t)), remark=remark))
    #                 for m in request.form.getlist('measure'): db.session.add(RemarkMeasure(topic=MeasureTopic.query.get(int(m)), remark=remark))
    #                 remark.measure_note = request.form['measure_note']
    #                 remark.subject_note = request.form['subject_note']
    #         db.session.commit()
    #     except Exception as e:
    #         log.error(u'Could not edit remarks {}'.format(e))
    #         flash_plus(u'Kan opmerkingen niet aanpassen', e)
    #
    #
    # students = set()
    # remarks = []
    # try:
    #     cb_id_list = request.form.getlist('cb')
    #     for id in cb_id_list:
    #         remark = Remark.query.get(int(id))
    #         if remark:
    #             remarks.append(remark)
    #             students.add(remark.student)
    # except Exception as e:
    #     log.error(u'Could not edit remarks : {}'.format(e))
    #     flash_plus(u'Kan de opmerkingen niet aanpassen', e)
    #     return redirect(url_for('remarks.show'))
    #
    # form_remark = RemarkForm()
    # return render_template('remark/remark.html',
    #                        subject = 'remarks',
    #                        save_filters=None,
    #                        save_remarks=remarks,
    #                        form_remark=form_remark,
    #                        students=students)

MAX_REMARKS_PER_MONTH = 5
MAX_REMARKS_PER_WEEK = 3

match_periods = [
    (MAX_REMARKS_PER_MONTH, lambda i : (i.timestamp + datetime.timedelta(days=29)).replace(hour=23, minute=59)),
    (MAX_REMARKS_PER_WEEK, lambda i : (i.timestamp + datetime.timedelta(days=6)).replace(hour=23, minute=59)),
]

#Per student, get all remarks which are not reviewed yet (review==False) and order by date (oldest first)
#Take the first remark off the list, add to r_match, and calculate last_date, i.e. timestamp + 30 (or +7) => sliding window
#Iterate over the remaining remarks and add to r_match when its timestamp falls in the window, break if there are
#no remarks anymore or timestamp falls outside the window
#If the number of remarks in r_match >= 5 (or 3), add the list of remarks to match_temp
#ELSE add the first remark to r_temp and copy it to r_match
#Remove these remarks in r_match from the original list
#Repeat for this student to check if there are more matches.  If so, add the remarks to match_temp or r_temp
#If all remarks of this student are checked, add all remark-lists in r_temp to matched_remarks, together with the student
#AND add the remaining remarks to non_matched_remarks

#From non_matched_remarks, filter out the remarks that cannot participate in a future match because it timestamps are too old
#Take the newest remark in the list and calculate the first_date, i.e. timestamp - 30
#Iterate over the list, from old to new, and mark an remark as REVIEWED if its timestamp is older then first_date

dummy_extra_match = {'id' : -1, 'note': ''}

@remarks.route('/remarks/start_review', methods=['GET', 'POST'])
@login_required
def start_review():
    try:
        schoolyear = calculate_current_schoolyear() if request.form['schoolyear'] == '' else request.form['schoolyear']
        students = db.session.query(Student).join(Remark).filter(Remark.reviewed == False, Student.schoolyear == schoolyear). \
            distinct(Remark.student_id).order_by(Student.last_name, Student.first_name).all()
        matched_remarks = []
        non_matched_remarks = []
        reviewed_remarks = []
        match_id = 0
        for s in students:
            match_temp = []
            remarks = Remark.query.filter(Remark.reviewed == False, Remark.student == s).order_by(Remark.timestamp).all()
            #First, try to find remarks in a period of 30 days, then in a period of 7 days
            for max_remarks, calculate_last_date in match_periods:
                r_match = []    #temporary to store remarks in the period
                r_temp = []
                while remarks:
                    r_first = remarks.pop(0)
                    r_match.append(r_first)
                    last_date = calculate_last_date(r_first)
                    for r in remarks:
                        if r.timestamp <= last_date:
                            r_match.append(r)
                        else:
                            break
                    if len(r_match) >= max_remarks:
                        extra_measure = r_match[0].extra_measure if r_match[0].extra_measure else dummy_extra_match
                        match_temp.append((match_id, extra_measure, r_match))
                        match_id += 1
                        del remarks[:len(r_match) - 1]
                    else:
                        r_temp.append(r_first) #no match, store for later use
                    r_match = []
                remarks = r_temp
            non_matched_remarks += remarks
            if match_temp:
                matched_remarks.append((s, match_temp))
            #check if some remarks need their reviewed_flag set to TRUE
            if remarks:
                first_date = (remarks[-1].timestamp - datetime.timedelta(days=30)).replace(hour=0, minute=1)
                for r in remarks:
                    if r.timestamp < first_date:
                        r.reviewed_flag=True
                        r2 = Remark.query.get(r.id)
                        r2.reviewed=True
                        reviewed_remarks.append(r)
        for r in reviewed_remarks:
             non_matched_remarks.remove(r)
        db.session.commit()
        if matched_remarks:
            for s, rll in matched_remarks:
                for id, extra_measure, rl in rll:
                    for r in rl:
                        r.print_date = r.timestamp.strftime('%d-%m-%Y %H:%M')
                        r.print_subjects = r.ret_subjects()
                        r.print_measures = r.ret_measures()
            for r in  non_matched_remarks:
                r.print_date = r.timestamp.strftime('%d-%m-%Y %H:%M')
                r.print_subjects = r.ret_subjects()
                r.print_measures = r.ret_measures()
    except Exception as e:
        log.error(u'Could not prepare the review : {}'.format(e))
        flash_plus(u'Kan de controle niet voorbereiden', e)
        return redirect(url_for('remarks.show'))

    return render_template('remark/review.html',
                        matched_remarks=matched_remarks,
                        non_matched_remarks=non_matched_remarks,
                        selected_schoolyear=schoolyear)


@remarks.route('/remarks/add_extra_measure/<string:remark_ids>/<string:em>', methods=['GET', 'POST'])
@login_required
def add_extra_measure(remark_ids, em):
    try:
        rid_list = json.loads(remark_ids)
        r = Remark.query.get(int(rid_list[0]))
        em = em.replace('&47;', '/')
        if r.extra_measure is not None:
            r.extra_measure.note = em
        else:
            extra_measure = ExtraMeasure(note=em)
            db.session.add(extra_measure)
            db.session.commit()
            for rid in rid_list:
                r = Remark.query.get(int(rid))
                r.extra_measure = extra_measure
        db.session.commit()
    except Exception as e:
        log.error(u'Could not add extra measure : {}'.format(e))
        return jsonify({'status' : False})
    return jsonify({'status' : True})

@remarks.route('/remarks/delete_extra_measure/<int:remark_id>', methods=['GET', 'POST'])
@login_required
def delete_extra_measure(remark_id):
    try:
        r = Remark.query.get(remark_id)
        db.session.delete(r.extra_measure)
        db.session.commit()
    except Exception as e:
        log.error(u'Could not delete extra measure : {}'.format(e))
        return jsonify({'status' : False})
    return jsonify({'status' : True})

@remarks.route('/remarks/review_done', methods=['GET', 'POST'])
@login_required
def review_done():
    try:
        remarks = Remark.query.filter(Remark.extra_measure_id != None, Remark.reviewed == False).all()
        for r in remarks:
            r.reviewed = True
        db.session.commit()
    except Exception as e:
         log.error(u'Could not set the remarks in reviewed state : {}'.format(e))

    return redirect(url_for('reviewed.show'), code=307)

