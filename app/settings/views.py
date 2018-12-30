# -*- coding: utf-8 -*-
# app/settings/views.py

from flask import render_template, redirect, url_for, request, flash, send_file, abort, jsonify
from flask_login import login_required, current_user
from ..base import get_global_setting_current_schoolyear, set_global_setting_current_schoolyear, get_setting_simulate_dayhour, set_setting_simulate_dayhour
from . import settings
from .. import db, app, log, admin_required
from ..models import Settings, Classgroup, Student, Teacher, Lesson, Classmoment
from flask_login import current_user
from ..documents import  get_doc_path, get_doc_list, upload_doc, get_doc_select, get_doc_download, get_doc_reference

import os, datetime
import unicodecsv  as  csv
import zipfile

def get_settings_and_show():
    schoolyear = get_global_setting_current_schoolyear()
    find_student = None
    try:
        find_student = Student.query.filter(Student.schoolyear == schoolyear).first()
        find_timetable = Classmoment.query.filter(Classmoment.schoolyear == schoolyear).first()
        schoolyears = Student.query.with_entities(Student.schoolyear).distinct().order_by(Student.schoolyear).all()
        if schoolyears:
            schoolyear_list = [int(i) for i,  in schoolyears]
        else:
            now = datetime.datetime.now()
            reference = datetime.datetime(year=now.year, month=9, day=1)
            now_year = int(str(now.year)[2:4])
            if now < reference:
                year = (now_year-1)*100 + now_year
            else:
                year = now_year*100 + now_year+1
            schoolyear_list = [year]
        last = schoolyear_list[-1]
        schoolyear_list.append(last+101)
    except Exception as e:
        log.error('Could not check the database for students or timetables, error {}'.format(e))

    return render_template('settings/settings.html',
                            students_already_in_database = True if find_student else False,
                            timetable_already_in_database = True if find_timetable else False,
                            schoolyear = schoolyear,
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

@settings.route('/settings/purge_database', methods=['GET', 'POST'])
@admin_required
@login_required
def purge_database():
    try:
        if 'delete_list' in request.form:
            pass
            # for d in document_type_list:
            #     if d in request.form['delete_doc']:
            #         if get_doc_select(d) in request.form:
            #             for i in request.form.getlist(get_doc_select(d)):
            #                 os.remove(os.path.join(get_doc_path(d), i))
    except Exception as e:
        flash('Kan niet verwijderen...')
    return redirect(url_for('admin.show'))


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
        log.info('Uploaded photos')
        flash('Fotos zijn geimporteerd')

    except Exception as e:
        flash('Kan bestand niet importeren')
    return redirect(url_for('settings.show'))


#NAAM           last_name
#VOORNAAM       first_name
#LEERLINGNUMMER number
#FOTO           photo
#KLAS           classgroup_id

def import_students(rfile):
    try:
        # format csv file :
        log.info('Import students from : {}'.format(rfile))
        students_file = csv.DictReader(rfile,  delimiter=';', encoding='utf-8-sig')

        nbr_students = 0
        nbr_classgroups = 0
        schoolyear = get_global_setting_current_schoolyear()

        for s in students_file:
            #skip empy records
            if s['VOORNAAM'] != '' and s['NAAM'] != '' and s['LEERLINGNUMMER'] != '' and s['FOTO'] != '':
                #check for classgroup.  If it not exists, add it first
                classgroup = Classgroup.query.filter(Classgroup.name==s['KLAS']).first()
                if not classgroup:
                    classgroup = Classgroup(name=s['KLAS'])
                    db.session.add(classgroup)
                    nbr_classgroups += 1
                #add student, if not already present
                find_student=Student.query.filter(Student.number==int(s['LEERLINGNUMMER']),
                                                        Student.schoolyear==schoolyear).first()
                if find_student:
                    #check if the student has a different photo or has changed classgroup
                    #If so update
                    if find_student.photo != s['FOTO']:
                        find_student.photo = s['FOTO']
                    if find_student.classgroup != classgroup:
                        find_student.classgroup = classgroup
                else:
                    student = Student(first_name=s['VOORNAAM'], last_name=s['NAAM'], number=int(s['LEERLINGNUMMER']), photo=s['FOTO'], classgroup=classgroup, schoolyear=schoolyear)
                    db.session.add(student)
                    nbr_students += 1

        db.session.commit()
        log.info('import: added {} students and {} classgroups'.format(nbr_students, nbr_classgroups))
        flash('Leerlingen zijn geimporteerd')

    except Exception as e:
        flash('Kan bestand niet importeren')
        log.error('cannot import : {}'.format(e))
    return redirect(url_for('settings.show'))

#FAMILIENAAM    last_name
#VOORNAAM       first_name
#CODE           code

def import_teachers(rfile):
    try:
        # format csv file :
        log.info('Import teachers from : {}'.format(rfile))
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
        log.info('import: added {} teachers'.format(nbr_teachers))
        flash('Leerkrachten zijn geimporteerd')

    except Exception as e:
        flash('Kan bestand niet importeren')
    return redirect(url_for('settings.show'))

#VOLGNUMMER
#KLAS           Classgroup.name
#LEERKRACHT     Teacher.name
#VAK            Lesson.name
#LOKAAL
#DAG            Classmoment.day
#UUR            Classmoment.hour

def import_timetable(rfile):
    try:
        # format csv file :
        log.info('Import timetable from : {}'.format(rfile))
        timetable_file = csv.DictReader(rfile,  delimiter=';', encoding='utf-8-sig')

        nbr_classmoments = 0
        nbr_lessons = 0
        schoolyear = get_global_setting_current_schoolyear()

        for t in timetable_file:
            #skip empy records
            if t['KLAS'] != '' and t['LEERKRACHT'] != '' and t['VAK'] != '' and t['DAG'] != '' and t['UUR'] != '':
                find_teacher = Teacher.query.filter(Teacher.code == t['LEERKRACHT']).first()
                if find_teacher:
                    find_classgroup = Classgroup.query.filter(Classgroup.name == t['KLAS']).first()
                    if find_classgroup:
                        #add lesson, if not already present
                        lesson = Lesson.query.filter(Lesson.name == t['VAK']).first()
                        if not lesson:
                            lesson =  Lesson(name=t['VAK'])
                            db.session.add(lesson)
                            nbr_lessons += 1
                        find_classmoment = Classmoment.query.filter(Classmoment.day == int(t['DAG']), Classmoment.hour == int(t['UUR']),
                                                                    Classmoment.classgroup == find_classgroup, Classmoment.teacher == find_teacher,
                                                                    Classmoment.lesson == lesson, Classmoment.schoolyear == schoolyear).first()
                        if not find_classmoment:
                            classmoment = Classmoment(day = int(t['DAG']), hour = int(t['UUR']),
                                                    classgroup = find_classgroup, teacher = find_teacher, lesson = lesson, schoolyear = schoolyear)
                            db.session.add(classmoment)
                            nbr_classmoments += 1

                    else:
                        log.info('import timetable: classgroup not found {}'.format(t['KLAS']))
                else:
                    log.info('import timetable: teacher not found: {}'.format(t['LEERKRACHT']))

        db.session.commit()
        log.info('import: added {} classmoments and {} lessons'.format(nbr_classmoments, nbr_lessons))
        flash('Lesrooster is geimporteerd')

    except Exception as e:
        flash('Kan bestand niet importeren')
    return redirect(url_for('settings.show'))

@settings.route('/settings/delete_students', methods=['GET', 'POST'])
@admin_required
@login_required
def delete_students():
    schoolyear = get_global_setting_current_schoolyear()
    try:
        students = Student.query.filter(Student.schoolyear==schoolyear).all()
        for s in students:
            db.session.delete(s)
        db.session.commit()
    except Exception as e:
        log.error('Could not not delete students from {}, error {}'.format(schoolyear, e))
        flash("Kan studenten van jaar {} niet wissen".format(schoolyear))

    log.info('Deleted students')
    flash("Studenten van jaar {} zijn gewist".format(schoolyear))
    return redirect(url_for('settings.show'))

@settings.route('/settings/delete_timetable', methods=['GET', 'POST'])
@admin_required
@login_required
def delete_timetable():
    schoolyear = get_global_setting_current_schoolyear()
    try:
        classmoments = Classmoment.query.filter(Classmoment.schoolyear==schoolyear).all()
        for c in classmoments:
            db.session.delete(c)
        db.session.commit()
    except Exception as e:
        log.error('Could not not delete classmoments from {}, error {}'.format(schoolyear, e))
        flash("Kan lesrooster van jaar {} niet wissen".format(schoolyear))

    log.info('Deleted timetable')
    flash("Lesrooster van jaar {} is gewist".format(schoolyear))
    return redirect(url_for('settings.show'))

