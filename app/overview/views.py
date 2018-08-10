# -*- coding: utf-8 -*-
# app/asset/views.py

from flask import render_template, redirect, url_for, request, flash, send_file, session
from flask_login import login_required, current_user

from .forms import ViewForm, OffenceForm
from .. import db, log
from . import overview
from ..models import Classgroup, Student, Offence, Type, Measure, Teacher, Classmoment, Lesson
from ..base import get_global_setting_current_schoolyear

from ..documents import get_doc_path
import os

#from ..base import build_filter, get_ajax_table, get_setting_inc_index_asset_name
#from ..tables_config import  tables_configuration

import cStringIO, csv, re

def filter_classgroup():
    #filter on teacher, timeslot , classgroup and lesson
    #priority is as follows:
    #- if teacher is changed: determine timeslot from current time and find classgroup and lesson from timetable
    #- if timeslot is changed: from teacher and timeslot determine classgroup and lesson from timetable
    #- if classgroup is changed : from teacher, timeslot and classgroup, try to determine lesson from timetable.
    #                             If this does not work, pick first available lesson for that classgroup
    #- if lesson is changed : go with the flow... :-)
    if 'classgroup' in request.form:
        classgroup = request.form['classgroup']
    else:
        classgroup = '3A'
    students = Student.query.join(Classgroup).filter(Classgroup.name==classgroup, Student.schoolyear==get_global_setting_current_schoolyear()).all()
    form = ViewForm()
    form.classgroup.data=classgroup
    return form, students

#show an overview of a classgroup
@overview.route('/overview', methods=['GET', 'POST'])
@login_required
def show():
    try:
        if 'button' in request.form and request.form['button'] == 'Bewaar':
            types = request.form.getlist('type')
            measures = request.form.getlist('measure')
            teacher = Teacher.query.filter(Teacher.code == request.form['teacher']).first()
            d, h = Classmoment.decode_dayhour(request.form['dayhour'])
            lesson = Lesson.query.join(Classmoment).filter(Classmoment.day == d, Classmoment.hour == h)
            #iterate over all students involved.  Create an offence per student.
            #link the measures and offence-types to the offence
            for s in request.form.getlist('student_id'):
                student = Student.query.filter(Student.id == int(s)).first()
                if student:
                    #save new offence
                    offence = Offence()
    except Exception as e:
        flash('Kan overtredingen niet opslaan')
    form, students = filter_classgroup()
    return render_template('overview/overview.html', form=form, students=students)


#a number of students are selected
@overview.route('/overview/new_offence', methods=['GET', 'POST'])
@login_required
def new_offence():
    students = []
    for s in request.form.getlist('student_id'):
        student = Student.query.filter(Student.id == int(s)).first()
        if student:
            print('geselecteeerd : {} {}'.format(student.first_name, student.last_name))
            students.append(student)

    form_filter, not_used_student = filter_classgroup()
    form_offence = OffenceForm(measure='test')
    return render_template('overview/offence.html', form_filter=form_filter, form_offence=form_offence, students=students)

