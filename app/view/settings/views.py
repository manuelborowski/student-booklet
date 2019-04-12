# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, request, json, jsonify
from flask_login import login_required
from app.database.settings import get_global_setting_sim_dayhour, get_global_setting_sim_dayhour_state, \
    set_global_setting_sim_dayhour, set_global_setting_sim_dayhour_state
from app.utils.base import get_academic_year, flash_plus
from . import settings
from app import db, log, admin_required, supervisor_required
from app.database.models import Grade, Student, Teacher, Lesson, Schedule, Remark, RemarkSubject, RemarkMeasure, ExtraMeasure, SubjectTopic, MeasureTopic
#from app.database.base import db_get_hub
from app.database import base
from app.utils.documents import  get_doc_path, get_doc_reference
from app.database.remarks import db_filter_remarks_to_be_reviewed, db_add_extra_measure, db_tag_remarks_as_reviewed

import os, datetime, random
import unicodecsv  as  csv
import zipfile

def get_settings_and_show():
    try:
        academic_year_list=base.db_hub_get_all_academic_years()
        academic_year_list=academic_year_list if academic_year_list else [get_academic_year()]
        last=academic_year_list[-1]
        academic_year_list.append(last+101)
        hub=base.db_get_hub()
        topics=[]
        measure_topics=MeasureTopic.query.filter(MeasureTopic.hub==hub).order_by(MeasureTopic.topic).all()
        mt_list=[{'id' : i.id, 'enabled' : i.enabled, 'topic' : i.topic} for i in measure_topics]
        topics.append(('measure_topic', 'Maatregelen', mt_list))
        subject_topics=SubjectTopic.query.filter(SubjectTopic.hub==hub).order_by(SubjectTopic.topic).all()
        st_list=[{'id' : i.id, 'enabled' : i.enabled, 'topic' : i.topic} for i in subject_topics]
        topics.append(('subject_topic', 'Opmerkingen', st_list))

        settings={}
        settings['sim_dayhour']=get_global_setting_sim_dayhour()
        settings['sim_dayhour_state']=get_global_setting_sim_dayhour_state()
    except Exception as e:
        log.error(u'Could not check the database for students or timetables, error {}'.format(e))
        flash_plus(u'Er is een fout opgetreden bij het ophalen van de instellingen', e)

    return render_template(u'settings/settings.html',
                            settings=settings,
                            academic_year_list=academic_year_list,
                            topics=topics,
                            title='settings')

@settings.route('/settings', methods=['GET', 'POST'])
@supervisor_required
@login_required
def show():
    return get_settings_and_show()

@settings.route('/settings/save', methods=['GET', 'POST'])
@admin_required
@login_required
def save():
    if request.files:
        if 'upload_students' in request.files:
            upload_students(request.files['upload_students'])
        elif 'upload_teachers' in request.files:
            upload_teachers(request.files['upload_teachers'])
        elif 'upload_schedule' in request.files:
            upload_schedule(request.files['upload_schedule'])
        elif 'upload_photos' in request.files:
            upload_photos(request.files['upload_photos'])
    elif request.form['save_subject']=='add_test_students':
        add_test_students()
    elif request.form['save_subject']=='delete_test_students':
        delete_test_students()
    elif request.form['save_subject']=='delete_students':
        delete_students()
    elif request.form['save_subject']=='delete_schedule':
        delete_schedule()
    elif 'txt_sim_dayhour' in request.form:
        save_sim_dayhour()
    return redirect(url_for('settings.show'))


def save_sim_dayhour():
    try:
        set_global_setting_sim_dayhour_state('chkb_sim_dayhour' in request.form)
        set_global_setting_sim_dayhour(request.form['txt_sim_dayhour'])
    except Exception as e:
        log.error(u'Cannot save simulate dayhour: {}'.format(e))
        flash_plus(u'Kan simulatie dag en uur niet bewaren', e)
    return

#NO PHOTOS ARE REMOVED, PHOTOS ARE ADDED ONLY
#upload and unzip a zipfile with photos
#if the same zipfile is uploaded with MORE photos then the additional photos are just added
#if the same zipfile is uploaded with LESS photos then NO photos are removed
def upload_photos(rfile):
    try:
        log.info('Upload photos from : {}'.format(rfile))
        #students_file=csv.DictReader(request.files['import_filename'],  delimiter=';', encoding='utf-8-sig')
        filename=get_doc_reference('photo').save(rfile, name=rfile.filename)
        zip_file=os.path.join(get_doc_path('photo'), filename)
        zip_ref=zipfile.ZipFile(zip_file, 'r')
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

#NO STUDENTS ARE REMOVED, STUDENTS ARE ADDED ONLY
#students are identified by an unique studentnumber
#if a list is uploaded again then it is checked if a student with the same studentnumber is already present
#if so, check if the grade or photo is changed.  If so, update grade or photo
def upload_students(rfile):
    try:
        # format csv file :
        log.info(u'Import students from : {}'.format(rfile))

        #students_file=csv.DictReader(rfile, delimiter=';', encoding='utf-8-sig') #utf-8 encoding
        students_file=csv.DictReader(rfile, delimiter=';', encoding='latin_1') #ansi encoding

        nbr_students=0
        academic_year=request.form['selected_academic_year']
        db_grades=base.db_grade_get_grades()
        grades={g.code: g.id for g in db_grades }
        hub=base.db_get_hub(academic_year=academic_year)

        if grades:
            for s in students_file:
                #skip empy records
                if s['VOORNAAM'] !='' and s['NAAM'] !='' and s['LEERLINGNUMMER'] !='' and s['FOTO'] !='':
                    #check for grade.  If it not exists, skip
                    if s['KLAS'] in grades:
                        #add student, if not already present
                        find_student=Student.query.filter(Student.number==int(s['LEERLINGNUMMER'])).first()
                        if find_student:
                            find_student.photo=s['FOTO']
                            find_student.grade_id=grades[s['KLAS']]
                            find_student.hub=hub
                        else:
                            student=Student(first_name=s['VOORNAAM'], last_name=s['NAAM'], number=int(s['LEERLINGNUMMER']),
                                              photo=s['FOTO'], grade_id=grades[s['KLAS']], hub=hub)
                            db.session.add(student)
                            nbr_students +=1
            db.session.commit()
        else:
            log.error('Error, no grades present yet')
            flash_plus('Fout, er zijn nog geen klassen ingeladen')

        log.info(u'import: added {} students'.format(nbr_students))
        flash_plus(u'{} leerlingen zijn geïmporteerd'.format(nbr_students))

    except Exception as e:
        flash_plus(u'Kan bestand niet importeren', e)
        log.error(u'cannot import : {}'.format(e))
    return

#FAMILIENAAM    last_name
#VOORNAAM       first_name
#CODE           code

#NO TEACHERS ARE REMOVED, TEACHERS ARE ADDED ONLY
def upload_teachers(rfile):
    try:
        # format csv file :
        log.info(u'Import teachers from : {}'.format(rfile))
        #teachers_file=csv.DictReader(rfile,  delimiter=';', encoding='utf-8-sig')
        teachers_file=csv.DictReader(rfile, delimiter=';', encoding='latin_1') #ansi encoding
        nbr_teachers=0
        for t in teachers_file:
            #skip empy records
            if t['VOORNAAM'] !='' and t['FAMILIENAAM'] !='' and t['CODE'] !='':
                #add teacher, if not already present
                find_teacher=Teacher.query.filter(Teacher.first_name==t['VOORNAAM'], Teacher.last_name==t['FAMILIENAAM'],
                                                    Teacher.code==t['CODE']).first()
                if not find_teacher:
                    teacher=Teacher(first_name=t['VOORNAAM'], last_name=t['FAMILIENAAM'], code=t['CODE'])
                    db.session.add(teacher)
                    nbr_teachers +=1

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

#REMOVE OLD SCHEDULE AND UPLOAD NEW SCHEDULE
#if a grade does not exist yet, add it
#if a lesson does not exist yet, add it
def upload_schedule(rfile):
    try:
        # format csv file :
        log.info(u'Import timetable from : {}'.format(rfile))
        academic_year=request.form['selected_academic_year']

        #first, delete current timetable
        delete_classmoments(academic_year)

        fieldnames=['VOLGNUMMER', 'KLAS', 'LEERKRACHT', 'VAK', 'LOKAAL', 'DAG', 'UUR' ]
        timetable_file=csv.DictReader(rfile,  fieldnames=fieldnames, delimiter=',', encoding='utf-8-sig')
        nbr_classmoments=0
        nbr_lessons=0
        error_message=''
        nbr_grades=0
        hub_sa=base.db_get_hub(academic_year=academic_year)
        hub_s=base.db_get_hub()

        for t in timetable_file:
            #skip empy records
            if t['KLAS'] !='' and t['LEERKRACHT'] !='' and t['VAK'] !='' and t['DAG'] !='' and t['UUR'] !='':
                find_teacher=Teacher.query.filter(Teacher.code==t['LEERKRACHT']).first()
                if find_teacher:
                    grade_code=t['KLAS'][:2] #leave out the grade

                    # check for grade.  If it not exists, add it first
                    find_grade=Grade.query.filter(Grade.code==grade_code).first()
                    if not find_grade:
                        find_grade=Grade(code=grade_code, hub=hub_s)
                        db.session.add(find_grade)
                        nbr_grades +=1
                    #add lesson, if not already present
                    lesson=Lesson.query.filter(Lesson.code==t['VAK']).first()
                    if not lesson:
                        lesson=Lesson(code=t['VAK'], hub=hub_s)
                        db.session.add(lesson)
                        nbr_lessons +=1
                    find_classmoment=Schedule.query.filter(Schedule.day==int(t['DAG']), Schedule.hour==int(t['UUR']),
                                                             Schedule.grade==find_grade, Schedule.teacher==find_teacher,
                                                             Schedule.lesson==lesson, Schedule.hub==hub_sa).first()
                    if not find_classmoment:
                        classmoment=Schedule(day=int(t['DAG']), hour=int(t['UUR']),
                                               grade=find_grade, teacher=find_teacher, lesson=lesson, hub=hub_sa)
                        db.session.add(classmoment)
                        nbr_classmoments +=1
                else:
                    log.info(u'import timetable: teacher not found: {}'.format(t['LEERKRACHT']))
                    error_message +=u'{} : niet gevonden<br>'.format(t['LEERKRACHT'])

        db.session.commit()
        log.info(u'import: added {} classmoments, {} grades and {} lessons'.format(nbr_classmoments, nbr_grades, nbr_lessons))
        if error_message=='':
            flash_plus(u'Lesrooster is geïmporteerd, {} lestijden, {} klassen en {} lessen toegevoegd'.format(nbr_classmoments, nbr_grades,  nbr_lessons))
        else:
            flash_plus(u'Lesrooster kan niet worden geïmporteerd', format(error_message))

    except Exception as e:
        flash_plus(u'Kan bestand niet importeren', e)
    return

def delete_students():
    academic_year=request.form['selected_academic_year']
    hub=base.db_get_hub()
    try:
        extra_measures=ExtraMeasure.query.join(Remark, Student).filter(Student.hub==hub).all()
        for em in extra_measures:
            db.session.delete(em)
        students=Student.query.filter(Student.hub==hub).all()
        for s in students:
            db.session.delete(s)
        db.session.commit()
        log.info(u'Deleted students')
        flash_plus(u'Studenten van jaar {} zijn gewist'.format(academic_year))
    except Exception as e:
        log.error(u'Could not not delete students from {}, error {}'.format(academic_year, e))
        flash_plus(u'Kan studenten van jaar {} niet wissen'.format(academic_year), e)
    return redirect(url_for('settings.show'))


def delete_classmoments(academic_year):
    hub=base.db_get_hub()
    classmoments=Schedule.query.filter(Schedule.hub==hub).all()
    for c in classmoments:
        db.session.delete(c)
    db.session.commit()


def delete_schedule():
    academic_year=request.form['selected_academic_year']
    try:
        delete_classmoments(request.form['selected_academic_year'])
        log.info(u'Deleted timetable')
        flash_plus(u'Lesrooster van jaar {} is gewist'.format(academic_year))
    except Exception as e:
        log.error(u'Could not not delete classmoments from {}, error {}'.format(academic_year, e))
        flash_plus(u'Kan lesrooster van jaar {} niet wissen'.format(academic_year), e)
    return redirect(url_for('settings.show'))

remark_dates=[
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '1/3', '13/3', '15/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '1/3', '13/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '13/3', '15/3', '19/3', '21/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '1/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '1/3', '2/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '10/2', '11/3', '19/3', '21/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '10/2', '15/2', '16/2', '23/3', '27/3'],
]

def add_test_students():
    academic_year=request.form['selected_academic_year']
    nbr_test_students=int(request.form['nbr-test-students'])
    add_extra_measure='chkb-extra-measure' in request.form
    hub=base.db_get_hub(academic_year=academic_year, test=True)
    random.seed()
    try:
        classmoments=Schedule.query.join(Grade).join(Lesson).join(Teacher).all()
        students_query=Student.query.filter(Student.academic_year==academic_year)
        students=students_query.all()

        for i in range(nbr_test_students):
            student=random.choice(students)
            dates=remark_dates[i % len(remark_dates)]
            for d in dates:
                classmoment=random.choice(classmoments)
                h=random.randint(10, 16)
                m=random.randint(1, 50)
                timestamp=datetime.datetime.strptime('{}/20{} {}:{}'.format(d, academic_year[2:4], h, m), '%d/%m/%Y %H:%M')
                remark=Remark(student=student, grade=student.grade, timestamp=timestamp,
                                 lesson=classmoment.lesson, teacher=classmoment.teacher, measure_note='', subject_note='TESTOPMERKING', hub=hub,
                                extra_attention=random.choice([True, False, False, False]))
                s=random.choice(base.db_subject_topic_get_list())
                m=random.choice(base.db_measure_topic_get_list())
                subject=RemarkSubject(topic=s, remark=remark)
                measure=RemarkMeasure(topic=m, remark=remark)
                db.session.add(subject)
                db.session.add(measure)
                db.session.add(remark)

        if add_extra_measure:
            matched_remarks, non_matched_remarks=db_filter_remarks_to_be_reviewed(academic_year, test=True, commit=False)
            for s, rll in matched_remarks:
                for id, extra_measure, rl in rll:
                    rids=[i.id for i in rl]
                    db_add_extra_measure(rids, 'TEST: extra sanctie voor {} {}'.format(s.first_name, s.last_name), commit=False)
        db_tag_remarks_as_reviewed()
        log.info(u'Added test students/remarks')
        flash_plus(u'Test studenten toegevoegd voor jaar {} '.format(academic_year))
    except Exception as e:
        log.error(u'Could not add test students error {}'.format(e))
        flash_plus(u'Kan test studenten voor jaar {} niet toevoegen'.format(academic_year), e)
    return redirect(url_for('settings.show'))

def delete_test_students():
    academic_year=request.form['selected_academic_year']
    try:
        hub = base.db_get_hub(academic_year=academic_year, test=True)
        remarks=Remark.query.filter(Remark.hub==hub).all()
        for r in remarks:
            if r.extra_measure and r.first_remark:
                db.session.delete(r.extra_measure)
            db.session.delete(r)
        db.session.commit()
        log.info(u'Removed test remarks')
        flash_plus(u'Test opmerkingen verwijderd voor jaar {} '.format(academic_year))
    except Exception as e:
        log.error(u'Could not delete test remarks error {}'.format(e))
        flash_plus(u'Kan test opmerkingen voor jaar {} niet verwijderen'.format(academic_year), e)
    return redirect(url_for('settings.show'))


@settings.route('/settings/add_topic/<string:subject>/<string:topic>', methods=['GET', 'POST'])
@supervisor_required
@login_required
def add_topic(subject, topic):
    try:
        hub=base.db_get_hub()
        if subject=='measure_topic':
            topic=MeasureTopic(topic=topic, hub=hub)
        elif subject=='subject_topic':
            topic=SubjectTopic(topic=topic,hub=hub)
        db.session.add(topic)
        db.session.commit()
    except Exception as e:
        log.error(u'Could not add {}, topic {}: {}'.format(subject, topic, e))
        flash_plus(u'Kan onderwerp niet toevoegen', e)
    return redirect(url_for('settings.show'))


@settings.route('/settings/set_topic_status/<string:data>', methods=['GET', 'POST'])
@supervisor_required
@login_required
def set_topic_status(data):
    try:
        jd=json.loads(data)
        ti=jd['id'].split('-')
        id=int(ti[1])
        if ti[0]=='measure_topic':
            topic=MeasureTopic.query.get(int(ti[1]))
        elif ti[0]=='subject_topic':
            topic=SubjectTopic.query.get(int(ti[1]))
        topic.enabled=jd['status']
        db.session.commit()
    except Exception as e:
        log.error('could not change the status')
        return jsonify({"status" : False})

    return jsonify({"status" : True})
