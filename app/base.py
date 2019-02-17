# -*- coding: utf-8 -*-

import datetime
from flask import flash, request
from models import Teacher, Schedule, Grade, Lesson, Student
from base_settings import get_global_setting_sim_dayhour_state, get_global_setting_sim_dayhour
from . import db, log

def get_all_schoolyears_from_database():
    schoolyears = Student.query.with_entities(Student.schoolyear).distinct().order_by(Student.schoolyear).all()
    return [int(i) for i, in schoolyears]


def calculate_current_schoolyear():
    now = datetime.datetime.now()
    reference = datetime.datetime(year=now.year, month=9, day=1)
    now_year = int(str(now.year)[2:4])
    if now < reference:
        year = (now_year - 1) * 100 + now_year
    else:
        year = now_year * 100 + now_year + 1
    return year

def get_timeslot_from_current_time():
    TT = [
        (8*60+30,  8*60+30+50,     1), #first hour : 8:30 till 9:20
        (9*60+20,  9*60+20+50+15,  2), #the break counts as timeslot 2
        (10*60+25, 10*60+25+50,    3),
        (11*60+15, 11*60+15+50,    4),
        (12*60+5,  12*60+5+55,     5),
        (13*60+0,  13*60+0+50,     6),
        (13*60+50, 13*60+50+50+15, 7), #the break counts as timeslot 7
        (14*60+55, 14*60+55+50,    8),
        (15*60+45, 15*60+45+50 +15*60+55,    9), #the whole evening and morning count as timeslot 9
    ]

    TT_W = [
        (8*60+30,  8*60+30+50,     1), #first hour : 8:30 till 9:20
        (9*60+20,  9*60+20+50+10,  2), #the break counts as timeslot 2
        (10*60+20, 10*60+20+50,    3),
        (11*60+10, 11*60+10+50+20*60+30,    4), #the whole evening and morning count as timeslot 4
    ]

    if get_global_setting_sim_dayhour_state():
        try:
            dh = get_global_setting_sim_dayhour().split('/')
            day = int(dh[0])
            m = int(dh[1]) * 60 + int(dh[2])
        except:
            log.error('bad sim dayhour string : {}'.format(get_global_setting_sim_dayhour()))
            now = datetime.datetime.now()
            day = now.weekday() + 1
            m = now.hour * 60 + now.minute
    else:
        now = datetime.datetime.now()
        day = now.weekday()+1
        m = now.hour * 60 + now.minute

    if day > 5: return 5, 9 #no school, return friday last hour
    tt = TT_W if day == 3 else TT
    for t in tt:
        if m >= t[0] and m < t[1]: return day, t[2]
    return 1, 1 #not found, return monday, first hour



def filter_overview(teacher_id, dayhour_str, grade_id, lesson_id, changed_item=None):
    #filter on teacher, timeslot , grade and lesson
    #priority is as follows:
    #- if teacher is changed: determine timeslot from current time and find grade and lesson from timetable
    #- if timeslot is changed: from teacher and timeslot determine grade and lesson from timetable
    #                             If this does not work, pick first grade for that teacher
    #- if grade is changed : from teacher, timeslot and grade, try to determine lesson from timetable.
    #                             If this does not work, pick first available lesson for that grade
    #- if lesson is changed : go with the flow... :-)
    teacher = None
    grade = None
    lesson = None
    d = 0
    h = 0

    if changed_item:
        teacher = Teacher.query.get(teacher_id)
    else:
        #teacher = Teacher.query.distinct(Teacher.code).order_by(Teacher.code).first()
        schedule = db.session.query(Schedule.teacher_id).distinct().first()
        teacher = Teacher.query.filter(Teacher.id==schedule.teacher_id).first()
        changed_item = 'teacher'

    if changed_item == 'teacher':
        d, h = get_timeslot_from_current_time()
        #try to find the classmoment, equal to or earlier than the given day and hour
        schedules = Schedule.query.join(Teacher).filter(Teacher.id == teacher.id).order_by(Schedule.day.desc(), Schedule.hour.desc()).all()
        dh = d * 10 + h
        for schedule in schedules:
            if dh >= schedule.day * 10 + schedule.hour: break
        else: schedule = None
        if not schedule:
            schedule = Schedule.query.join(Teacher).filter(Teacher.id == teacher.id).order_by(Schedule.day, Schedule.hour).first()
        if schedule:
            d = schedule.day
            h = schedule.hour
        #dayhour_str = '{}/{}'.format(d,h)
        changed_item = 'dayhour'
    else:
        d, h = Schedule.decode_dayhour(dayhour_str)

    if changed_item == 'dayhour':
        #fetch grade from timetable
        schedule = Schedule.query.join(Teacher).filter(Schedule.day == d, Schedule.hour == h, Teacher.id == teacher.id).first()
        if schedule:
            #the classmoment points to a single teacher, grade and lesson
            return schedule
        # find the first grade, teached by given teacher
        grade = Grade.query.join(Schedule).join(Teacher).filter(Teacher.id == teacher.id).distinct(Grade.code).order_by(Grade.code).first()
        if not grade:
            #just pick the first grade from all grades
            grade = Grade.query.distinct(Grade.code).order_by(Grade.code).first()
        changed_item = 'grade'
    else:
        grade = Grade.query.get(grade_id)

    if changed_item == 'grade':
        #find the first lesson, taken by given grade
        lesson = Lesson.query.join(Schedule).join(Grade).join(Teacher).filter(Grade.id == grade.id, Teacher.id == teacher.id)\
                .distinct(Lesson.code).order_by(Lesson.code).first()
        if not lesson:
            #just pick the first lesson
            lesson = Lesson.query.distinct(Lesson.code).order_by(Lesson.code).first()
    else:
        lesson = Lesson.query.get(lesson_id)

    #create a dummy classmoment
    schedule = Schedule(day=d, hour=h, schoolyear = calculate_current_schoolyear(), teacher=teacher, lesson=lesson, grade=grade)
    return schedule

def filter_duplicates_out(keep_list, filter_list):
    keep_list.append(('disabled', '--------'))
    for i in filter_list:
        if not i in keep_list:
            keep_list.append(i)
    return keep_list

#It is possible to give an extra (exception) message
#The python UTF-8 string is encoded to html UTF-8
def flash_plus(message, e=None):
    if e:
        flash((u'{}<br><br>Details:<br>{}'.format(message, e)).encode('ascii', 'xmlcharrefreplace'))
    else:
        flash((u'{}'.format(message)).encode('ascii', 'xmlcharrefreplace'))

def button_save_pushed():
    return 'button' in request.form and request.form['button'] == 'save'

