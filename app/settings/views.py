# -*- coding: utf-8 -*-
# app/settings/views.py

from flask import render_template, redirect, url_for, request, flash, send_file, abort
from flask_login import login_required, current_user
from ..base import get_setting_inc_index_asset_name, set_setting_inc_index_asset_name, get_setting_copy_from_last_add, set_setting_copy_from_last_add
from . import settings
from .. import db, app, log
from ..models import Settings, Classgroup, Student, Teacher, Lesson, Classmoment
from flask_login import current_user
from ..documents import  get_doc_path, get_doc_list, upload_doc, get_doc_select, get_doc_download, get_doc_reference

import os
import unicodecsv  as  csv
import zipfile

def check_admin():
    if not current_user.is_admin:
        abort(403)

def get_settings_and_show():
    #inc_index_asset_name : if true and this asset is used as base to copy from, then the index of the asset name
    #will be incremented by one
    inc_index_asset_name = get_setting_inc_index_asset_name()
    #copy_from_last_add : if a url-shortcut with qr code is uses, and the qr code is not found, then a new asset is
    #added which is a copy from the previous added asset.
    copy_from_last_add = get_setting_copy_from_last_add()
    return render_template('settings/settings.html',
                           inc_index_asset_name=inc_index_asset_name,
                           copy_from_last_add=copy_from_last_add,
                           title='settings')

@settings.route('/settings', methods=['GET', 'POST'])
@login_required
def show():
    return get_settings_and_show()

@settings.route('/settings/save', methods=['GET', 'POST'])
@login_required
def save():
    if request.form['button'] == 'Bewaar':
        set_setting_inc_index_asset_name(True if 'inc_index_asset_name' in request.form else False)
        set_setting_copy_from_last_add(True if 'copy_from_last_add' in request.form else False)

    return get_settings_and_show()

@settings.route('/settings/purge_database', methods=['GET', 'POST'])
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
                find_student=Student.query.filter(Student.first_name==s['VOORNAAM'], Student.last_name==s['NAAM'],
                                                          Student.number==int(s['LEERLINGNUMMER']),
                                                          Student.photo==s['FOTO'], Student.classgroup==classgroup).first()
                if not find_student:
                    student = Student(first_name=s['VOORNAAM'], last_name=s['NAAM'], number=int(s['LEERLINGNUMMER']), photo=s['FOTO'], classgroup=classgroup)
                    db.session.add(student)
                    nbr_students += 1

        db.session.commit()
        log.info('import: added {} students and {} classgroups'.format(nbr_students, nbr_classgroups))
        flash('Leerlingen zijn geimporteerd')

    except Exception as e:
        flash('Kan bestand niet importeren')
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
                                                                    Classmoment.lesson == lesson).first()
                        if not find_classmoment:
                            classmoment = Classmoment(day = int(t['DAG']), hour = int(t['UUR']),
                                                    classgroup = find_classgroup, teacher = find_teacher, lesson = lesson)
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