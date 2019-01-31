# -*- coding: utf-8 -*-

from flask import render_template, url_for, request, redirect, jsonify
from flask_login import login_required, current_user

from .. import db, log, app
from . import offences
from ..models import Offence, Type, Measure, Student, ExtraMeasure
from ..forms import OffenceForm
from ..base_multiple_items import build_filter_and_filter_data, prepare_data_for_html
from ..base import calculate_current_schoolyear, flash_plus
from ..tables_config import  tables_configuration

import datetime, json

#This will make the variable 'schoolyear' default available in all templates
@app.context_processor
def inject_schoolyear():
    return dict(schoolyear=calculate_current_schoolyear())

#This will make the variable 'schoolyear' default available in all templates
@app.context_processor
def inject_url_rule():
    return dict(url_rule=request.url_rule)

@offences.route('/offences/data', methods=['GET', 'POST'])
@login_required
def source_data():
    only_checkbox_for = current_user.username if current_user.is_strict_user else None
    ajax_table =  prepare_data_for_html(tables_configuration['offence'], only_checkbox_for=only_checkbox_for)
    return ajax_table

@offences.route('/offences', methods=['GET', 'POST'])
@login_required
def show():
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
            log.error(u'Could not edit offences {}'.format(e))
            flash_plus(u'Kan opmerkingen niet aanpassen', e)
    #The following line is required only to build the filter-fields on the page.
    _filter, _filter_form, a,b, c = build_filter_and_filter_data(tables_configuration['offence'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['offence'])

@offences.route('/offences/delete', methods=['GET', 'POST'])
@login_required
def delete():
    try:
        cb_id_list = request.form.getlist('cb')
        for id in cb_id_list:
            offence = Offence.query.get(int(id))
            if offence: db.session.delete(offence)
        db.session.commit()
    except Exception as e:
        log.error(u'Could not delete offence : {}'.format(e))
        flash_plusu('Kan de opmerkingen niet verwijderen', e)
    #The following line is required only to build the filter-fields on the page.
    _filter, _filter_form, a,b, c = build_filter_and_filter_data(tables_configuration['offence'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['offence'])

@offences.route('/offences/edit', methods=['GET', 'POST'])
@login_required
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
        log.error(u'Could not edit offences : {}'.format(e))
        flash_plus(u'Kan de opmerkingen niet aanpassen', e)
        return redirect(url_for('offences.show'))

    form_offence = OffenceForm()
    return render_template('offence/offence.html',
                           redirect_url = url_for('offences.show'),
                           save_filters=None,
                           save_offences=offences,
                           form_offence=form_offence,
                           students=students)

MAX_OFFENCES_PER_MONTH = 5
MAX_OFFENCES_PER_WEEK = 3

match_periods = [
    (MAX_OFFENCES_PER_MONTH, lambda i : (i.timestamp + datetime.timedelta(days=29)).replace(hour=23, minute=59)),
    (MAX_OFFENCES_PER_WEEK, lambda i : (i.timestamp + datetime.timedelta(days=6)).replace(hour=23, minute=59)),
]

#Per student, get all offences which are not reviewed yet (review==False) and order by date (oldest first)
#Take the first offence off the list, add to o_match, and calculate last_date, i.e. timestamp + 30 (or +7) => sliding window
#Iterate over the remaining offences and add to o_match when its timestamp falls in the window, break if there are
#no offences anymore or timestamp falls outside the window
#If the number of offences in o_match >= 5 (or 3), add the list of offences to match_temp
#ELSE add the first offence to o_temp and copy it to o_match
#Remove these offences in o_match from the original list
#Repeat for this student to check if there are more matches.  If so, add the offences to match_temp or o_temp
#If all offences of this student are checked, add all offence-lists in o_temp to matched_offences, together with the student
#AND add the remaining offences to non_matched_offences

#From non_matched_offences, filter out the offences that cannot participate in a future match because it timestamps are too old
#Take the newest offence in the list and calculate the first_date, i.e. timestamp - 30
#Iterate over the list, from old to new, and mark an offence as REVIEWED if its timestamp is older then first_date

dummy_extra_match = {'id' : -1, 'note': ''}

@offences.route('/offences/start_review', methods=['GET', 'POST'])
@login_required
def start_review():
    try:
        schoolyear = calculate_current_schoolyear() if request.form['schoolyear'] == '' else request.form['schoolyear']
        students = db.session.query(Student).join(Offence).filter(Offence.reviewed==False, Student.schoolyear==schoolyear). \
            distinct(Offence.student_id).order_by(Student.last_name, Student.first_name).all()
        matched_offences = []
        non_matched_offences = []
        reviewed_offences = []
        match_id = 0
        for s in students:
            match_temp = []
            offences = Offence.query.filter(Offence.reviewed==False, Offence.student==s).order_by(Offence.timestamp).all()
            #First, try to find offences in a period of 30 days, then in a period of 7 days
            for max_offences, calculate_last_date in match_periods:
                o_match = []    #temporary to store offences in the period
                o_temp = []
                while offences:
                    o_first = offences.pop(0)
                    o_match.append(o_first)
                    last_date = calculate_last_date(o_first)
                    for o in offences:
                        if o.timestamp <= last_date:
                            o_match.append(o)
                        else:
                            break
                    if len(o_match) >= max_offences:
                        #extra_measure = o_match[0].extra_measure.note if o_match[0].extra_measure is not None else ''
                        extra_measure = o_match[0].extra_measure if o_match[0].extra_measure else dummy_extra_match
                        match_temp.append((match_id, extra_measure, o_match))
                        match_id += 1
                        del offences[:len(o_match) - 1]
                    else:
                        o_temp.append(o_first) #no match, store for later use
                    o_match = []
                offences = o_temp
            non_matched_offences += offences
            if match_temp:
                matched_offences.append((s, match_temp))
            #check if some offences need their reviewed_flag set to TRUE
            if offences:
                first_date = (offences[-1].timestamp - datetime.timedelta(days=30)).replace(hour=0, minute=1)
                for o in offences:
                    if o.timestamp < first_date:
                        o.reviewed_flag=True
                        o2 = Offence.query.get(o.id)
                        o2.reviewed=True
                        reviewed_offences.append(o)
        for o in reviewed_offences:
             non_matched_offences.remove(o)
        db.session.commit()
        if matched_offences:
            for s, oll in matched_offences:
                for id, extra_measure, ol in oll:
                    for o in ol:
                        o.print_date = o.timestamp.strftime('%d-%m-%Y %H:%M')
                        o.print_types = o.ret_types()
                        o.print_measures = o.ret_measures()
            for o in  non_matched_offences:
                o.print_date = o.timestamp.strftime('%d-%m-%Y %H:%M')
                o.print_types = o.ret_types()
                o.print_measures = o.ret_measures()
    except Exception as e:
        log.error(u'Could not prepare the review : {}'.format(e))
        flash_plus(u'Kan de controle niet voorbereiden', e)
        return redirect(url_for('offences.show'))

    return render_template('offence/review.html',
                        matched_offences=matched_offences,
                        non_matched_offences=non_matched_offences,
                        selected_schoolyear=schoolyear)


@offences.route('/offences/add_measure/<string:oids>/<string:em>', methods=['GET', 'POST'])
@login_required
def add_measure(oids, em):
    try:
        oid_list = json.loads(oids)
        o = Offence.query.get(int(oid_list[0]))
        em = em.replace('&47;', '/')
        if o.extra_measure is not None:
            o.extra_measure.note = em
        else:
            extra_measure = ExtraMeasure(note=em)
            db.session.add(extra_measure)
            db.session.commit()
            for oid in oid_list:
                o = Offence.query.get(int(oid))
                o.extra_measure = extra_measure
        db.session.commit()
    except Exception as e:
        log.error(u'Could not add extra measure : {}'.format(e))
        return jsonify({'status' : False})

    return jsonify({'status' : True})

@offences.route('/offences/delete_measure/<int:offence_id>', methods=['GET', 'POST'])
@login_required
def delete_measure(offence_id):
    try:
        o = Offence.query.get(offence_id)
        db.session.delete(o.extra_measure)
        db.session.commit()
    except Exception as e:
        log.error(u'Could not delete extra measure : {}'.format(e))
        return jsonify({'status' : False})

    return jsonify({'status' : True})

@offences.route('/offences/match_reviewed/<int:offence_id>', methods=['GET', 'POST'])
@login_required
def match_reviewed(offence_id):
    try:
        em = Offence.query.get(offence_id).extra_measure
        if em:
            for o in em.offences:
                o.reviewed = True
        db.session.commit()
    except Exception as e:
        log.error(u'Could not set the offences in reviewed state : {}'.format(e))
        return jsonify({'status' : False})

    return redirect(url_for('review.start_review'))
    return jsonify({'status' : True})


@offences.route('/offences/review_done', methods=['GET', 'POST'])
@login_required
def review_done():
    try:
        offences = Offence.query.filter(Offence.measure_id != None, Offence.reviewed == False).all()
        for o in offences:
            o.reviewed = True
        db.session.commit()
    except Exception as e:
         log.error(u'Could not set the offences in reviewed state : {}'.format(e))

    return redirect(url_for('reviewed.show'), code=307)

