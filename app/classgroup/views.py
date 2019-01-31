# -*- coding: utf-8 -*-

from flask import render_template, url_for, request
from flask_login import login_required

from .forms import ViewForm
from .. import db, log
from . import classgroup
from ..models import Classgroup, Student, Offence, Type, Measure, Teacher, Classmoment, Lesson
from ..base import  filter_overview, filter_duplicates_out, calculate_current_schoolyear, flash_plus
from ..forms import OffenceForm
import datetime

def filter_classgroup():
    try :
        if 'change_id' in request.form:
            classmoment = filter_overview(int(request.form['teacher']), request.form['dayhour'], int(request.form['classgroup']), int(request.form['lesson']), request.form['change_id'])
        else:
            classmoment = filter_overview(0, 0, 0, 0) #default settings

        students = Student.query.join(Classgroup).\
            filter(Classgroup.id==classmoment.classgroup.id, Student.schoolyear==calculate_current_schoolyear()).all()
        teacher_classgroups = Classgroup.get_choices_filtered_by_teacher_list(classmoment.teacher)
        teacher_lessons = Lesson.get_choices_filtered_by_teacher_list(classmoment.teacher)

        #update default option
        form = ViewForm()
        form.teacher.data=str(classmoment.teacher.id)
        form.dayhour.data=classmoment.get_data_day_hour()
        form.classgroup.data=str(classmoment.classgroup.id)
        form.classgroup.choices = filter_duplicates_out(teacher_classgroups + form.classgroup.choices)
        form.lesson.data=str(classmoment.lesson.id)
        form.lesson.choices = filter_duplicates_out(teacher_lessons + form.lesson.choices)
    except Exception as e:
        log.error(u'Cannot filter the classgroup {}'.format(e))
        flash_plus(u'Er is een probleem met de filter', e)
        return ViewForm(), []
    return form, students

@classgroup.route('/classgroup', methods=['GET', 'POST'])
@login_required
def show():
    try:
        if 'button' in request.form and request.form['button'] == 'Bewaar':
            types = request.form.getlist('type')
            measures = request.form.getlist('measure')
            teacher = Teacher.query.filter(Teacher.id == request.form['teacher']).first()
            d, h = Classmoment.decode_dayhour(request.form['dayhour'])
            lesson = Lesson.query.filter(Lesson.id == request.form['lesson']).first()
            #iterate over all students involved.  Create an offence per student.
            #link the measures and offence-types to the offence
            for s in request.form.getlist('student_id'):
                student = Student.query.get(int(s))
                if student:
                    #save new offence
                    offence = Offence(student=student, lesson=lesson, teacher=teacher, timestamp=datetime.datetime.now(),
                                      measure_note=request.form['comment_measure'], type_note=request.form['comment_offence'],
                                      classgroup=student.classgroup)
                    for t in types:
                        type=Type(type=int(t), offence=offence)
                        db.session.add(type)
                    for m in measures:
                        measure=Measure(measure=int(m), offence=offence)
                        db.session.add(measure)
                    db.session.add(offence)
            db.session.commit()
    except Exception as e:
        flash_plus(u'Kan overtredingen niet opslaan', e)
        log.error(u'Cannot save remarks {}'.format(e))
    form, students = filter_classgroup()
    return render_template('classgroup/classgroup.html', form=form, students=students)


@classgroup.route('/classgroup/new_offence', methods=['GET', 'POST'])
@login_required
def new_offence():
    students = []
    for s in request.form.getlist('student_id'):
        student = Student.query.filter(Student.id == int(s)).first()
        if student:
            students.append(student)
    form_filter, not_used_student = filter_classgroup()
    form_offence = OffenceForm()
    return render_template('offence/offence.html',
                           redirect_url = url_for('classgroup.show'),
                           save_filters=form_filter,
                           save_offences=None,
                           form_offence=form_offence,
                           students=students)

