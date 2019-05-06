# -*- coding: utf-8 -*-

from app.database import db_utils, db_schedule
from app.database.db_utils import db_get_timeslot_from_current_time
from app.database.models import Teacher, Schedule, Grade, Lesson, Classgroup
from app import db


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
