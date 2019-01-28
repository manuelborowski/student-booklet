import datetime
from models import Teacher, Classmoment, Classgroup, Lesson, Student
from base_settings import get_setting_simulate_dayhour

def get_all_schoolyears_from_database():
    schoolyears = Student.query.with_entities(Student.schoolyear).distinct().order_by(Student.schoolyear).all()
    return [''] + [i for i, in schoolyears]


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
        (8*60+30,  8*60+30+50,  1),   #first hour : 8:30 till 9:20
        (9*60+20,  9*60+20+50,  2),
        (10*60+25, 10*60+25+50, 3),
        (11*60+15, 11*60+15+50, 4),
        (12*60+5,  12*60+5+55,  5),
        (13*60+0,  13*60+0+50,  6),
        (13*60+50, 13*60+50+50, 7),
        (14*60+55, 15*60+55+50, 8),
        (15*60+45, 15*60+45+50, 9),
    ]

    TT_W = [
        (8*60+30,  8*60+30+50,  1),   #first hour : 8:30 till 9:20
        (9*60+20,  9*60+20+50,  2),
        (10*60+20, 10*60+20+50, 3),
        (11*60+10, 11*60+10+50, 4),
    ]

    simulate_dayhour = get_setting_simulate_dayhour()
    if simulate_dayhour != '0/0':
        return Classmoment.decode_dayhour(simulate_dayhour)

    now = datetime.datetime.now()
    day = now.weekday()+1
    if day > 5: return 1, 1 #no school, return monday, first hour
    tt = TT_W if day == 3 else TT
    m = now.hour * 60 + now.minute
    for t in tt:
        if m >= t[0] and m < t[1]: return day, t[2]
    return 1, 1 #not found, return monday, first hour



def filter_overview(teacher_id, dayhour_str, classgroup_id, lesson_id, changed_item=None):
    #filter on teacher, timeslot , classgroup and lesson
    #priority is as follows:
    #- if teacher is changed: determine timeslot from current time and find classgroup and lesson from timetable
    #- if timeslot is changed: from teacher and timeslot determine classgroup and lesson from timetable
    #                             If this does not work, pick first classgroup for that teacher
    #- if classgroup is changed : from teacher, timeslot and classgroup, try to determine lesson from timetable.
    #                             If this does not work, pick first available lesson for that classgroup
    #- if lesson is changed : go with the flow... :-)
    teacher = None
    classgroup = None
    lesson = None
    d = 0
    h = 0

    if changed_item:
        teacher = Teacher.query.get(teacher_id)
        classgroup = Classgroup.query.get(classgroup_id)
        lesson = Lesson.query.get(lesson_id)
        d, h = Classmoment.decode_dayhour(dayhour_str)
    else:
        teacher = Teacher.query.distinct(Teacher.code).order_by(Teacher.code).first()
        changed_item = 'teacher'

    if changed_item == 'teacher':
        d, h = get_timeslot_from_current_time()
        #if default day and hour (1, 1) is returned, try to find the first avaible lesmoment for given teacher
        classmoment = Classmoment.query.join(Teacher).filter(Teacher.id == teacher.id).order_by(Classmoment.day, Classmoment.hour).first()
        if classmoment:
            d = classmoment.day
            h = classmoment.hour
        #dayhour_str = '{}/{}'.format(d,h)
        changed_item = 'dayhour'

    if changed_item == 'dayhour':
        #fetch classgroup from timetable
        classmoment = Classmoment.query.join(Teacher).filter(Classmoment.day == d, Classmoment.hour == h, Teacher.id == teacher.id).first()
        if classmoment:
            #the classmoment points to a single teacher, classgroup and lesson
            print(classmoment)
            return classmoment
        # find the first classgroup, teached by given teacher
        classgroup = Classgroup.query.join(Classmoment).join(Teacher).filter(Teacher.id == teacher.id).distinct(Classgroup.name).order_by(Classgroup.name).first()
        if not classgroup:
            #just pick the first classgroup from all classgroups
            classgroup = Classgroup.query.distinct(Classgroup.name).order_by(Classgroup.name).first()
        changed_item = 'classgroup'

    if changed_item == 'classgroup':
        #find the first lesson, taken by given classgroup
        lesson = Lesson.query.join(Classmoment).join(Classgroup).join(Teacher).filter(Classgroup.id == classgroup.id, Teacher.id == teacher.id)\
                .distinct(Lesson.name).order_by(Lesson.name).first()
        if not lesson:
            #just pick the first lesson
            lesson = Lesson.query.distinct(Lesson.name).order_by(Lesson.name).first()

    #create a dummy classmoment
    classmoment = Classmoment(day=d, hour=h, schoolyear = get_global_setting_current_schoolyear(), teacher=teacher, lesson=lesson, classgroup=classgroup)
    return classmoment

def filter_duplicates_out(in_list):
    out_list = []
    added = set()
    for val in in_list:
        if not val in added:
            out_list.append(val)
            added.add(val)
    return out_list