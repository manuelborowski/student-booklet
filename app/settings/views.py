# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, request
from flask_login import login_required
from ..base_settings import set_global_setting_current_schoolyear, get_setting_simulate_dayhour, set_setting_simulate_dayhour
from ..base import calculate_current_schoolyear, get_all_schoolyears_from_database, flash_plus
from . import settings
from .. import db, log, admin_required
from ..models import Grade, Student, Teacher, Lesson, Schedule, Remark, RemarkSubject, RemarkMeasure, ExtraMeasure
from ..documents import  get_doc_path, get_doc_reference

import os, datetime, random
import unicodecsv  as  csv
import zipfile

def get_settings_and_show():
    try:
        schoolyear_list = get_all_schoolyears_from_database()
        schoolyear_list = schoolyear_list if schoolyear_list else [calculate_current_schoolyear()]
        last = schoolyear_list[-1]
        schoolyear_list.append(last+101)
    except Exception as e:
        log.error(u'Could not check the database for students or timetables, error {}'.format(e))
        flash_plus(u'Er is een fout opgetreden bij het ophalen van de instellingen', e)

    return render_template(u'settings/settings.html',
                            simulate_dayhour = get_setting_simulate_dayhour(),
                            schoolyear_list = schoolyear_list,
                            title='settings')

@settings.route('/settings', methods=['GET', 'POST'])
@admin_required
@login_required
def show():
    return get_settings_and_show()

@settings.route('/settings/save', methods=['GET', 'POST'])
@admin_required
@login_required
def save():
    if 'select_schoolyear' in request.form:
        set_global_setting_current_schoolyear(request.form['select_schoolyear'])
    if 'save_settings' in request.form:
        if 'schoolyear' in request.form:
           set_global_setting_current_schoolyear(request.form['schoolyear'])
        if 'simulate_dayhour' in request.form:
            set_setting_simulate_dayhour(request.form['simulate_dayhour'])
    return get_settings_and_show()

@settings.route('/settings/upload_file', methods=['GET', 'POST'])
@admin_required
@login_required
def upload_file():
    if request.files['upload_students']: import_students(request.files['upload_students'])
    if request.files['upload_teachers']: import_teachers(request.files['upload_teachers'])
    if request.files['upload_timetable']: import_timetable(request.files['upload_timetable'])
    if request.files['upload_photos']: upload_photos(request.files['upload_photos'])
    return redirect(url_for('settings.show'))


def upload_photos(rfile):
    try:
        log.info('Upload photos from : {}'.format(rfile))
        #students_file = csv.DictReader(request.files['import_filename'],  delimiter=';', encoding='utf-8-sig')
        filename = get_doc_reference('photo').save(rfile, name=rfile.filename)
        zip_file = os.path.join(get_doc_path('photo'), filename)
        zip_ref = zipfile.ZipFile(zip_file, 'r')
        zip_ref.extractall(get_doc_path('photo'))
        zip_ref.close()
        log.info(u'Uploaded photos')
        flash_plus(u'Foto\'s zijn geïmporteerd')
    except Exception as e:
        log.error(u'Cannot import photos : {}'.format(e))
        flash_plus(u'Kan bestand niet importeren', e)
    return

#NAAM           last_name
#VOORNAAM       first_name
#LEERLINGNUMMER number
#FOTO           photo
#KLAS           grade_id

def import_students(rfile):
    try:
        # format csv file :
        log.info(u'Import students from : {}'.format(rfile))
        students_file = csv.DictReader(rfile,  delimiter=';', encoding='utf-8-sig')

        nbr_students = 0
        nbr_grades = 0
        schoolyear = request.form['select_schoolyear']

        for s in students_file:
            #skip empy records
            if s['VOORNAAM'] != '' and s['NAAM'] != '' and s['LEERLINGNUMMER'] != '' and s['FOTO'] != '':
                #check for grade.  If it not exists, add it first
                grade = Grade.query.filter(Grade.code == s['KLAS']).first()
                if not grade:
                    grade = Grade(code=s['KLAS'])
                    db.session.add(grade)
                    nbr_grades += 1
                #add student, if not already present
                find_student=Student.query.filter(Student.number==int(s['LEERLINGNUMMER']),
                                                        Student.schoolyear==schoolyear).first()
                if find_student:
                    #check if the student has a different photo or has changed grade
                    #If so update
                    if find_student.photo != s['FOTO']:
                        find_student.photo = s['FOTO']
                    if find_student.grade != grade:
                        find_student.grade = grade
                else:
                    student = Student(first_name=s['VOORNAAM'], last_name=s['NAAM'], number=int(s['LEERLINGNUMMER']), photo=s['FOTO'], grade=grade, schoolyear=schoolyear)
                    db.session.add(student)
                    nbr_students += 1
        db.session.commit()
        log.info(u'import: added {} students and {} grades'.format(nbr_students, nbr_grades))
        flash_plus(u'{} leerlingen en {} klassen zijn geïmporteerd'.format(nbr_students, nbr_grades))

    except Exception as e:
        flash_plus(u'Kan bestand niet importeren', e)
        log.error(u'cannot import : {}'.format(e))
    return

#FAMILIENAAM    last_name
#VOORNAAM       first_name
#CODE           code

def import_teachers(rfile):
    try:
        # format csv file :
        log.info(u'Import teachers from : {}'.format(rfile))
        teachers_file = csv.DictReader(rfile,  delimiter=';', encoding='utf-8-sig')
        nbr_teachers = 0
        for t in teachers_file:
            #skip empy records
            if t['VOORNAAM'] != '' and t['FAMILIENAAM'] != '' and t['CODE'] != '':
                #add teacher, if not already present
                find_teacher = Teacher.query.filter(Teacher.first_name==t['VOORNAAM'], Teacher.last_name==t['FAMILIENAAM'],
                                                    Teacher.code==t['CODE']).first()
                if not find_teacher:
                    teacher = Teacher(first_name=t['VOORNAAM'], last_name=t['FAMILIENAAM'], code=t['CODE'])
                    db.session.add(teacher)
                    nbr_teachers += 1

        db.session.commit()
        log.info(u'import: added {} teachers'.format(nbr_teachers))
        flash_plus(u'{} leerkrachten zijn geïmporteerd'.format(nbr_teachers))

    except Exception as e:
        flash_plus(u'Kan bestand niet importeren', e)
    return

#VOLGNUMMER
#KLAS           Classgroup.code
#LEERKRACHT     Teacher.code
#VAK            Lesson.code
#LOKAAL
#DAG            Classmoment.day
#UUR            Classmoment.hour

def import_timetable(rfile):
    try:
        # format csv file :
        log.info(u'Import timetable from : {}'.format(rfile))
        schoolyear = request.form['select_schoolyear']

        #first, delete current timetable
        delete_classmoments(schoolyear)

        timetable_file = csv.DictReader(rfile,  delimiter=';', encoding='utf-8-sig')
        nbr_classmoments = 0
        nbr_lessons = 0
        error_message = ''

        for t in timetable_file:
            #skip empy records
            if t['KLAS'] != '' and t['LEERKRACHT'] != '' and t['VAK'] != '' and t['DAG'] != '' and t['UUR'] != '':
                find_teacher = Teacher.query.filter(Teacher.code == t['LEERKRACHT']).first()
                if find_teacher:
                    grade = t['KLAS'][:2] #leave out the grade
                    find_grade = Grade.query.filter(Grade.code == grade).first()
                    if find_grade:
                        #add lesson, if not already present
                        lesson = Lesson.query.filter(Lesson.code == t['VAK']).first()
                        if not lesson:
                            lesson =  Lesson(code=t['VAK'])
                            db.session.add(lesson)
                            nbr_lessons += 1
                        find_classmoment = Schedule.query.filter(Schedule.day == int(t['DAG']), Schedule.hour == int(t['UUR']),
                                                                 Schedule.grade == find_grade, Schedule.teacher == find_teacher,
                                                                 Schedule.lesson == lesson, Schedule.schoolyear == schoolyear).first()
                        if not find_classmoment:
                            classmoment = Schedule(day = int(t['DAG']), hour = int(t['UUR']),
                                                   grade = find_grade, teacher = find_teacher, lesson = lesson, schoolyear = schoolyear)
                            db.session.add(classmoment)
                            nbr_classmoments += 1
                    else:
                        log.info(u'import timetable: grade not found {}'.format(grade))
                        error_message += u'{} : niet gevonden<br>'.format(grade)
                else:
                    log.info(u'import timetable: teacher not found: {}'.format(t['LEERKRACHT']))
                    error_message += u'{} : niet gevonden<br>'.format(t['LEERKRACHT'])

        db.session.commit()
        log.info(u'import: added {} classmoments and {} lessons'.format(nbr_classmoments, nbr_lessons))
        if error_message == '':
            flash_plus(u'Lesrooster is geïmporteerd, {} lestijden en {} lessen toegevoegd'.format(nbr_classmoments, nbr_lessons))
        else:
            flash_plus(u'Lesrooster kan niet worden geïmporteerd', format(error_message))

    except Exception as e:
        flash_plus(u'Kan bestand niet importeren', e)
    return

@settings.route('/settings/delete_students', methods=['GET', 'POST'])
@admin_required
@login_required
def delete_students():
    schoolyear = request.form['select_schoolyear']
    try:
        extra_measures = ExtraMeasure.query.join(Remark, Student).filter(Student.schoolyear == schoolyear).all()
        for em in extra_measures:
            db.session.delete(em)
        students = Student.query.filter(Student.schoolyear==schoolyear).all()
        for s in students:
            db.session.delete(s)
        db.session.commit()
        log.info(u'Deleted students')
        flash_plus(u'Studenten van jaar {} zijn gewist'.format(schoolyear))
    except Exception as e:
        log.error(u'Could not not delete students from {}, error {}'.format(schoolyear, e))
        flash_plus(u'Kan studenten van jaar {} niet wissen'.format(schoolyear), e)
    return redirect(url_for('settings.show'))

def delete_classmoments(schoolyear):
    classmoments = Schedule.query.filter(Schedule.schoolyear == schoolyear).all()
    for c in classmoments:
        db.session.delete(c)
    db.session.commit()

@settings.route('/settings/delete_timetable', methods=['GET', 'POST'])
@admin_required
@login_required
def delete_timetable():
    schoolyear = request.form['select_schoolyear']
    try:
        delete_classmoments(request.form['select_schoolyear'])
        log.info(u'Deleted timetable')
        flash_plus(u'Lesrooster van jaar {} is gewist'.format(schoolyear))
    except Exception as e:
        log.error(u'Could not not delete classmoments from {}, error {}'.format(schoolyear, e))
        flash_plus(u'Kan lesrooster van jaar {} niet wissen'.format(schoolyear), e)
    return redirect(url_for('settings.show'))

remark_dates = [
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '1/3', '13/3', '15/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '1/3', '13/3'],
    #['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '13/3', '15/3', '19/3', '21/3'],
    #['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '1/3'],
    #['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '1/3', '2/3'],
    #['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '10/2', '11/3', '19/3', '21/3'],
    #['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '10/2', '15/2', '16/2', '23/3', '27/3'],
]

@settings.route('/settings/add_test_students', methods=['GET', 'POST'])
@admin_required
@login_required
def add_test_students():
    schoolyear = request.form['select_schoolyear']
    random.seed()
    try:
        #fetch the first classmoment
        classmoments = Schedule.query.join(Grade).join(Lesson).join(Teacher).all()
        students = Student.query.join(Remark).filter(Student.first_name.like('TEST%'),
                                                     Student.last_name.like('TEST%'), Student.schoolyear == schoolyear).all()
        for s in students:
            for o in s.remarks:
                if o.extra_measure:
                    db.session.delete(o.extra_measure)
            #delete students/...
            db.session.delete(s)
        students = []
        for i, dates in enumerate(remark_dates):
            classmoment = random.choice(classmoments)
            student = Student(first_name='TEST{}'.format(i), last_name='TEST{}'.format(i), schoolyear=schoolyear,
                              grade=classmoment.grade)
            db.session.add(student)
            students.append(student)
            for d in dates:
                h = random.randint(10, 16)
                m = random.randint(1, 50)
                timestamp = datetime.datetime.strptime('{}/2018 {}:{}'.format(d, h, m), '%d/%m/%Y %H:%M')
                remark = Remark(student=student, grade=student.grade, timestamp=timestamp,
                                 lesson=classmoment.lesson, teacher=classmoment.teacher, measure_note='', subject_note='')
                t = random.randint(0, 5)
                m = random.randint(0, 4)
                subject = RemarkSubject(subject=t, remark=remark)
                measure = RemarkMeasure(measure=m, remark=remark)
                db.session.add(subject)
                db.session.add(measure)
                db.session.add(remark)
        db.session.commit()
        log.info(u'Added test students/remarks')
        flash_plus(u'Test studenten toegevoegd voor jaar {} '.format(schoolyear))
    except Exception as e:
        log.error(u'Could not add test students error {}'.format(e))
        flash_plus(u'Kan test studenten voor jaar {} niet toevoegen'.format(schoolyear), e)
    return redirect(url_for('settings.show'))

@settings.route('/settings/delete_test_students', methods=['GET', 'POST'])
@admin_required
@login_required
def delete_test_students():
    schoolyear = request.form['select_schoolyear']
    try:
        students = Student.query.join(Remark).filter(Student.first_name.like('TEST%'),
                                                     Student.last_name.like('TEST%'), Student.schoolyear == schoolyear).all()
        for s in students:
            for o in s.remarks:
                if o.extra_measure:
                    db.session.delete(o.extra_measure)
            #delete students/...
            db.session.delete(s)
        db.session.commit()
        log.info(u'Removed test students/remarks')
        flash_plus(u'Test studenten verwijderd voor jaar {} '.format(schoolyear))
    except Exception as e:
        log.error(u'Could not delete test students error {}'.format(e))
        flash_plus(u'Kan test studenten voor jaar {} niet verwijderen'.format(schoolyear), e)
    return redirect(url_for('settings.show'))

