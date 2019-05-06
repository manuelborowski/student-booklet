# -*- coding: utf-8 -*-

from flask import render_template, url_for, request, redirect
from flask_login import login_required, current_user
import datetime

import app.database.db_utils
from . import grade
from .forms import FilterForm
from app import db, log, app
from app.database import db_lesson, db_schedule, db_teacher, db_grade, db_student, db_utils, db_user, db_setting
from app.utils import utils
from app.database.models import Student, Remark, RemarkSubject, RemarkMeasure, Teacher, Schedule, Lesson, SubjectTopic, MeasureTopic
from app.layout.forms import RemarkForm


def filter_grade():
    try:
        if not current_user.in_schedule and not current_user.in_replacement and current_user.is_strict_user:
            log.error(u'Level 1 user not in schedule')
            utils.flash_plus(u'Sorry, u kan op deze pagina niets zien')
            return FilterForm(), []

        if 'change_id' in request.form:  # filters on grade-page are used
            teacher_id = int(request.form['teacher'])
            day_hour = request.form['dayhour']
            changed_item = request.form['change_id']
            try:
                lesson_id = int(request.form['lesson'])
            except:
                lesson_id = -1
            try:
                grade_id = int(request.form['grade'])
            except:
                grade_id = -1
            db_user.session_set_grade_filter(teacher_id, day_hour, grade_id, lesson_id, changed_item)
        teacher_id, day_hour, grade_id, lesson_id, changed_item = db_user.session_get_grade_filter()
        schedules = db_grade.db_filter_grade(teacher_id, day_hour, grade_id, lesson_id, changed_item)
    except Exception as e:
        log.error(u'No schedule found {}'.format(e))
        utils.flash_plus(u'Er is nog geen lesrooster geladen')
        return FilterForm(), []
    try:
        #put all students in one list and sort on last name
        students = []
        for s in schedules:
            students += db_student.db_student_list(classgroup=s.classgroup)
        students = sorted(students, key=lambda i: i.last_name)
        teacher_grades = db_grade.db_grade_list(schedules[0].teacher, html_select=True)
        is_single_grade, classgroup_codes = db_grade.db_single_grade(schedules)
        teacher_lessons = db_lesson.db_lesson_list(schedules[0].teacher, html_select=True)
        teacher_schedules = db_schedule.db_schedule_list(schedules[0].teacher, html_select=True)

        # create filter
        form_filter = FilterForm()
        form_filter.teacher.data = str(schedules[0].teacher.id)
        if current_user.is_at_least_supervisor:
            choices = db_teacher.db_teacher_list(select=True, full_name=True)
        elif current_user.teacher_list:
            choices = current_user.teacher_list
        else:
            choices = None
        form_filter.teacher.choices = choices

        form_filter.dayhour.data = schedules[0].get_data_day_hour()
        form_filter.dayhour.choices = utils.filter_duplicates_out(teacher_schedules, Schedule.get_choices_day_hour())

        if is_single_grade:
            form_filter.grade.data = str(schedules[0].classgroup.grade.id)
        else:
            teacher_grades.append(('disabled-unused', classgroup_codes))
            form_filter.grade.data = 'disabled-unused'
        form_filter.grade.choices = utils.filter_duplicates_out(teacher_grades, db_grade.db_grade_list(html_select=True))

        form_filter.lesson.data = str(schedules[0].lesson.id)
        form_filter.lesson.choices = utils.filter_duplicates_out(teacher_lessons, db_lesson.db_lesson_list(html_select=True))

        db_user.session_set_grade_filter(day_hour=schedules[0].get_data_day_hour(), grade_id=schedules[0].classgroup.grade.id, lesson_id=schedules[0].lesson.id)

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
            d, h = Schedule.decode_dayhour(request.form['dayhour'])
            ts_d, ts_h = db_utils.db_get_timeslot_from_current_time(include_zero_hour=True)
            delta_d = ts_d - d
            if d * 10 + h > ts_d * 10 + ts_h:
                delta_d += 7
            now = datetime.datetime.now()
            if db_setting.get_global_setting_sim_dayhour_state():
                try:
                    now = datetime.datetime.strptime(db_setting.get_global_setting_sim_dayhour(), '%d-%m-%Y %H:%M')
                except Exception as e:
                    log.error('bad sim dayhour string : {}'.format(e))
            date = (now - datetime.timedelta(days=delta_d)).strftime('%d-%m-%Y')
            students = []
            for s in request.form.getlist('student_id'):
                student = Student.query.get(s)
                if student:
                    students.append(student)
            form = RemarkForm()
            return render_template('remark/remark.html', subject='grade', action='add', form=form, students=students, hour=h, date=date)

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
                teacher_id, day_hour, grade_id, lesson_id, changed_item = db_user.session_get_grade_filter()
                subjects = request.form.getlist('subject')
                measures = request.form.getlist('measure')
                h, m = db_utils.timeslot_to_time(int(request.form['hour']))
                timestamp = datetime.datetime.strptime('{} {}:{}'.format(request.form['txt-date'], h, m), '%d-%m-%Y %H:%M')
                if current_user.teacher and current_user.is_strict_user:
                    teacher = current_user.teacher
                else:
                    teacher = Teacher.query.filter(Teacher.id == teacher_id, Teacher.school == db_utils.school()).first()
                lesson = db_lesson.db_lesson(lesson_id)
                # iterate over all students involved.  Create an remark per student.
                # link the measures and remark-subjects to the remark
                for s in request.form.getlist('student_id'):
                    student = Student.query.get(int(s))
                    if student:
                        # save new remark
                        remark = Remark(student=student, lesson=lesson, teacher=teacher, timestamp=timestamp,
                                        measure_note=request.form['measure_note'], subject_note=request.form['subject_note'],
                                        grade=student.classgroup.grade, extra_attention='chkb_extra_attention' in request.form,
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


