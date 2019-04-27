# -*- coding: utf-8 -*-
import datetime

from app.database import db_teacher, db_utils, db_schedule
from app.database.models import Teacher, Schedule, Grade, Lesson, Classgroup
from app import db, log
from app.database.db_setting import get_global_setting_sim_dayhour_state, get_global_setting_sim_dayhour


def db_filter_grade(teacher_id, dayhour_str, grade_id, lesson_id, changed_item=None):
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

    teacher = Teacher.query.get(teacher_id)

    if changed_item == 'teacher':
        d, h = db_get_timeslot_from_current_time()
        #try to find the classmoment, equal to or earlier than the given day and hour
        schedules_found = db_schedule.query_filter(Schedule.query.join(Teacher)).filter(Schedule.teacher == teacher)\
            .order_by(Schedule.day.desc(), Schedule.hour.desc()).all()
        dh = d * 10 + h
        for schedule in schedules_found:
            if dh >= schedule.day * 10 + schedule.hour: break
        else: schedule = None
        if not schedule:
            schedule = db_schedule.query_filter(Schedule.query.join(Teacher)).filter(Schedule.teacher == teacher).order_by(Schedule.day, Schedule.hour).first()
        if schedule:
            d = schedule.day
            h = schedule.hour
        changed_item = 'dayhour'
    else:
        d, h = Schedule.decode_dayhour(dayhour_str)

    if changed_item == 'dayhour':
        #fetch classgroups from timetable
        schedules = db_schedule.query_filter(Schedule.query.join(Teacher)).filter(Schedule.day == d, Schedule.hour == h, Schedule.teacher == teacher)\
            .order_by(Schedule.day, Schedule.hour).all()
        if schedules:
            #the classmoment points to a single teacher, grade and lesson
            return schedules
        #just pick the first grade from all grades
        grade = Grade.query.distinct(Grade.code).order_by(Grade.code).first()
        changed_item = 'grade'
    else:
        grade = Grade.query.get(grade_id)

    if changed_item == 'grade':
        #find the first lesson, taken by given grade
        lesson = db_schedule.query_filter(Lesson.query.join(Schedule, Lesson.id == Schedule.lesson_id)
                                          .join(Classgroup, Classgroup.id == Schedule.classgroup_id).join(Grade, Grade.id == Classgroup.grade_id)
                                          .join(Teacher, Teacher.id == Schedule.teacher_id))\
            .filter(Grade.id == grade.id, Schedule.teacher == teacher).distinct(Lesson.code).order_by(Lesson.code).first()
        if not lesson:
            #just pick the first lesson
            lesson = Lesson.query.filter(Lesson.school == db_utils.school()).distinct(Lesson.code).order_by(Lesson.code).first()
    else:
        lesson = Lesson.query.get(lesson_id)

    #create a dummy classmoment
    schedules = []
    classgroups = Classgroup.query.filter(Classgroup.grade == grade).all()
    for c in classgroups:
        schedules.append(Schedule(day=d, hour=h, school=db_utils.school(), academic_year=db_utils.academic_year(), teacher=teacher
                          , lesson=lesson, classgroup=c))
    return schedules


def db_get_timeslot_from_current_time():
    TT = [
        (0,        8*60+30,        10), #timeslot 9, of the previous day
        (8*60+30,  8*60+30+50,     1), #first hour : 8:30 till 9:20
        (9*60+20,  9*60+20+50+15,  2), #the break counts as timeslot 2
        (10*60+25, 10*60+25+50,    3),
        (11*60+15, 11*60+15+50,    4),
        (12*60+5,  12*60+5+55,     5),
        (13*60+0,  13*60+0+50,     6),
        (13*60+50, 13*60+50+50+15, 7), #the break counts as timeslot 7
        (14*60+55, 14*60+55+50,    8),
        (15*60+45, 24*60,          9), #the whole evening as timeslot 9
    ]

    TT_W = [
        (0,        8*60+30,        10), #timeslot 9 of the previous day
        (8*60+30,  8*60+30+50,     1), #first hour : 8:30 till 9:20
        (9*60+20,  9*60+20+50+10,  2), #the break counts as timeslot 2
        (10*60+20, 10*60+20+50,    3),
        (11*60+10, 24*60,          4), #the whole evening count as timeslot 4
    ]

    now = datetime.datetime.now()
    if get_global_setting_sim_dayhour_state():
        try:
            now = datetime.datetime.strptime(get_global_setting_sim_dayhour(), '%d-%m-%Y %H:%M')
        except Exception as e:
            log.error('bad sim dayhour string : {}'.format(e))
    day = now.weekday()+1
    m = now.hour * 60 + now.minute

    tt = TT_W if day == 3 else TT
    d = h = 1
    if day > 5: #no school, return friday last hour
        d = 5
        h = 9
    else:
        i = 0
        for t in tt:
            if t[0] <= m < t[1]:
                i = t[2]
                break
        if i == 0: #not found
            d = h = 1
        elif i == 10: #now is before 8:30 in the morning
            d = day - 1
            h = 9
            if d < 1:
                d = h = 1
        else: #now is after 8:30 in the morning
            h = i
            d = day
    return d, h

#input schedules : a list of schedules of a single teacher on a single classmoment
#a teacher can teach different classgroups overlapping different grades, e.g;
# Schedule: 12718/2/1/6B EMt1/ADRI/ENG,
# Schedule: 12721/2/1/6C MtWeA/ADRI/ENG,
# Schedule: 12724/2/1/6C MtWeB/ADRI/ENG,
# If this is the case, following is returned : False and '6B EMt1/6C MtWeA/6C MtWeB
#Else, True and '' is returend to indicate a complete grade is selected
def db_single_grade(schedules):
    single_grade = True
    temp_cg_codes = ''
    if schedules:
        grade = schedules[0].classgroup.grade
        for s in schedules:
            temp_cg_codes += s.classgroup.code + '/'
            if s.classgroup.grade != grade:
                single_grade = False
        if single_grade:
            classgroup_count = db.session.query(Classgroup).filter(Classgroup.grade == schedules[0].classgroup.grade).count()
            if len(schedules) != classgroup_count:
                single_grade = False
    return (True, '') if single_grade else (False, temp_cg_codes[:-1])


def db_grade_list(teacher=None, html_select=False, in_schedule=True):
    if html_select:
        q = db.session.query(Grade.id, Grade.code)
    else:
        q = Grade.query
    if teacher:
        q = db_schedule.query_filter(q.join(Classgroup, Grade.id == Classgroup.grade_id).join(Schedule, Schedule.classgroup_id == Classgroup.id))\
            .filter(Schedule.teacher == teacher)
    else:
        if in_schedule:
            q = db_schedule.query_filter(q.join(Classgroup, Grade.id == Classgroup.grade_id).join(Schedule))
        else:
            q = q.filter(Grade.school == db_utils.school())
    return q.distinct(Grade.code).order_by(Grade.code).all()
