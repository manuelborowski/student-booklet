# -*- coding: utf-8 -*-

from flask import render_template, url_for, request, redirect
from flask_login import login_required, current_user
import datetime

from . import grade
from .forms import FilterForm
from app import db, log
from app.database import db_lesson, db_schedule, db_teacher, db_grade, db_student, db_utils
from app.utils import utils
from app.database.models import Student, Remark, RemarkSubject, RemarkMeasure, Teacher, Schedule, Lesson, SubjectTopic, MeasureTopic
from app.layout.forms import RemarkForm


def filter_grade():
    try:
        teacher = db_teacher.db_teacher(code=current_user.username)
        teacher_found_in_schedule = not not db_schedule.db_schedule_list(teacher=teacher) if teacher else False
        if not teacher_found_in_schedule and current_user.is_strict_user:
            log.error(u'Level 1 user not in schedule')
            utils.flash_plus(u'Sorry, u kan op deze pagina niets zien')
            return FilterForm(), []

        if 'change_id' in request.form:  # filters on grade-page are used
            if request.form['dayhour'] == 'disabled' or request.form['grade'] == 'disabled' or request.form['lesson'] == 'disabled':
                schedule = db_grade.db_filter_grade(int(request.form['teacher']), '', 0, 0, 'teacher')
            else:
                # One of the items in the filter has changed
                schedule = db_grade.db_filter_grade(int(request.form['teacher']), request.form['dayhour'], int(request.form['grade']),
                                                    int(request.form['lesson']), request.form['change_id'])
        else:  # first time the grade-page is visited
            if teacher_found_in_schedule:
                schedule = db_grade.db_filter_grade(teacher.id, '', 0, 0, 'teacher')
            else:
                schedule = db_grade.db_filter_grade(0, 0, 0, 0)  # default settings
    except Exception as e:
        log.error(u'No schedule found {}'.format(e))
        utils.flash_plus(u'Er is nog geen lesrooster geladen')
        return FilterForm(), []
    try:
        students = db_student.db_student_list(grade=schedule.grade)
        teacher_grades = db_grade.db_grade_list(schedule.teacher, select=True)
        teacher_lessons = db_lesson.db_lesson_list(schedule.teacher, select=True)
        teacher_schedules = db_schedule.db_schedule_list(schedule.teacher, select=True)

        # update default option
        form_filter = FilterForm()
        form_filter.teacher.data = str(schedule.teacher.id)
        if teacher_found_in_schedule and current_user.is_strict_user:
            form_filter.teacher.choices = [(teacher.id, teacher.code)]
        else:
            form_filter.teacher.choices = db_teacher.db_teacher_list(select=True)

        form_filter.dayhour.data = schedule.get_data_day_hour()
        form_filter.dayhour.choices = utils.filter_duplicates_out(teacher_schedules, Schedule.get_choices_day_hour())

        form_filter.grade.data = str(schedule.grade.id)
        form_filter.grade.choices = utils.filter_duplicates_out(teacher_grades, db_grade.db_grade_list(select=True))

        form_filter.lesson.data = str(schedule.lesson.id)
        form_filter.lesson.choices = utils.filter_duplicates_out(teacher_lessons, db_lesson.db_lesson_list(select=True))

    except Exception as e:
        log.error(u'Cannot filter the grade {}'.format(e))
        utils.flash_plus(u'Er is een probleem met de filter', e)
        return FilterForm(), []
    return form_filter, students


@grade.route('/grade', methods=['GET', 'POST'])
@login_required
def show():
    form_filter, students = filter_grade()
    return render_template('grade/grade.html', form_filter=form_filter, students=students)


@grade.route('/grade/action', methods=['GET', 'POST'])
@login_required
def action():
    try:
        if utils.button_pressed('add'):
            students = []
            for s in request.form.getlist('student_id'):
                student = Student.query.get(s)
                if student:
                    students.append(student)
            form_filter, not_used_students = filter_grade()
            form = RemarkForm()
            return render_template('remark/remark.html', subject='grade', action='add', save_filters=form_filter, save_remarks=None,
                                   form=form, students=students)

    except Exception as e:
        utils.flash_plus(u'Kan opmerking niet opslaan', e)
        log.error(u'Cannot save remarks {}'.format(e))
    return redirect(url_for('grade.show'))

@grade.route('/grade/action_done/<string:action>/<int:id>', methods=['GET', 'POST'])
@grade.route('/grade/action_done/<string:action>', methods=['GET', 'POST'])
@login_required
def action_done(action=None, id=-1):
    try:
        if utils.button_pressed('save'):
            if action == 'add':
                subjects = request.form.getlist('subject')
                measures = request.form.getlist('measure')
                teacher = Teacher.query.filter(Teacher.id == request.form['teacher'], Teacher.school == db_utils.school()).first()
                d, h = Schedule.decode_dayhour(request.form['dayhour'])
                lesson = db_lesson.db_lesson(request.form['lesson'])
                # iterate over all students involved.  Create an remark per student.
                # link the measures and remark-subjects to the remark
                for s in request.form.getlist('student_id'):
                    student = Student.query.get(int(s))
                    if student:
                        # save new remark
                        remark = Remark(student=student, lesson=lesson, teacher=teacher, timestamp=datetime.datetime.now(),
                                        measure_note=request.form['measure_note'], subject_note=request.form['subject_note'],
                                        grade=student.grade, extra_attention='chkb_extra_attention' in request.form,
                                        school=db_utils.school(), academic_year=db_utils.academic_year())
                        for s in subjects:
                            subject = RemarkSubject(topic=SubjectTopic.query.get(int(s)), remark=remark)
                            db.session.add(subject)
                        for m in measures:
                            measure = RemarkMeasure(topic=MeasureTopic.query.get(int(m)), remark=remark)
                            db.session.add(measure)
                        db.session.add(remark)
                db.session.commit()
            return redirect(url_for('grade.show'))
    except Exception as e:
        utils.flash_plus(u'Kan opmerking niet opslaan', e)
        log.error(u'Cannot save remarks {}'.format(e))
    return redirect(url_for('grade.show'))


