# -*- coding: utf-8 -*-

from flask import render_template, url_for, request
from flask_login import login_required

from .forms import FilterForm
from .. import db, log
from . import grade
from ..models import Grade, Student, Remark, RemarkSubject, RemarkMeasure, Teacher, Schedule, Lesson
from ..base import  filter_overview, filter_duplicates_out, calculate_current_schoolyear, flash_plus
from ..forms import RemarkForm
import datetime

def filter_grade():
    try :
        if 'change_id' in request.form:
            if request.form['dayhour'] == 'disabled' or request.form['grade'] == 'disabled' or request.form['lesson'] == 'disabled':
                schedule = filter_overview(int(request.form['teacher']), '', 0, 0, 'teacher')
            else:
                schedule = filter_overview(int(request.form['teacher']), request.form['dayhour'], int(request.form['grade']), int(request.form['lesson']), request.form['change_id'])
        else:
            schedule = filter_overview(0, 0, 0, 0) #default settings
    except Exception as e:
        log.error(u'No schedule found {}'.format(e))
        flash_plus(u'Er is nog geen lesrooster geladen')
        return FilterForm(), []
    try:
        students = Student.query.join(Grade).\
            filter(Grade.id == schedule.grade.id, Student.schoolyear == calculate_current_schoolyear()).all()
        teacher_grades = Grade.get_choices_filtered_by_teacher_list(schedule.teacher)
        teacher_lessons = Lesson.get_choices_filtered_by_teacher_list(schedule.teacher)

        #update default option
        form_filter = FilterForm()
        form_filter.teacher.data=str(schedule.teacher.id)
        form_filter.teacher.choices = Schedule.get_teacher_choices_list()
        form_filter.dayhour.data=schedule.get_data_day_hour()
        form_filter.dayhour.choices = Schedule.get_choices_day_hour()
        form_filter.grade.data=str(schedule.grade.id)
        form_filter.grade.choices = filter_duplicates_out(teacher_grades, Schedule.get_grade_choices_list())
        form_filter.lesson.data=str(schedule.lesson.id)
        form_filter.lesson.choices = filter_duplicates_out(teacher_lessons, Lesson.get_choices_list())
    except Exception as e:
        log.error(u'Cannot filter the grade {}'.format(e))
        flash_plus(u'Er is een probleem met de filter', e)
        return FilterForm(), []
    return form_filter, students

@grade.route('/grade', methods=['GET', 'POST'])
@login_required
def show():
    try:
        if 'button' in request.form and request.form['button'] == 'Bewaar':
            subjects = request.form.getlist('subject')
            measures = request.form.getlist('measure')
            teacher = Teacher.query.filter(Teacher.id == request.form['teacher']).first()
            d, h = Schedule.decode_dayhour(request.form['dayhour'])
            lesson = Lesson.query.filter(Lesson.id == request.form['lesson']).first()
            #iterate over all students involved.  Create an remark per student.
            #link the measures and remark-subjects to the remark
            for s in request.form.getlist('student_id'):
                student = Student.query.get(int(s))
                if student:
                    #save new remark
                    remark = Remark(student=student, lesson=lesson, teacher=teacher, timestamp=datetime.datetime.now(),
                                     measure_note=request.form['measure_note'], subject_note=request.form['subject_note'],
                                     grade=student.grade)
                    for s in subjects:
                        subject=RemarkSubject(subject=int(s), remark=remark)
                        db.session.add(subject)
                    for m in measures:
                        measure=RemarkMeasure(measure=int(m), remark=remark)
                        db.session.add(measure)
                    db.session.add(remark)
            db.session.commit()
    except Exception as e:
        flash_plus(u'Kan opmerking niet opslaan', e)
        log.error(u'Cannot save remarks {}'.format(e))
    form_filter, students = filter_grade()
    return render_template('grade/grade.html', form_filter=form_filter, students=students)


@grade.route('/grade/new_remark', methods=['GET', 'POST'])
@login_required
def new_remark():
    students = []
    for s in request.form.getlist('student_id'):
        student = Student.query.filter(Student.id == int(s)).first()
        if student:
            students.append(student)
    form_filter, not_used_student = filter_grade()
    form_remark = RemarkForm()
    return render_template('remark/remark.html',
                           redirect_url = url_for('grade.show'),
                           save_filters=form_filter,
                           save_remarks=None,
                           form_remark=form_remark,
                           students=students)
