from flask import render_template, redirect, url_for, request, json, jsonify
from flask_login import login_required

from . import settings
from app import db, log, admin_required, supervisor_required

from app.utils import utils, documents
from app.database import db_measure_topic, db_subject_topic, db_setting, db_grade, db_remark, db_schedule, db_lesson

from app.database.models import Grade, Student, Teacher, Lesson, Schedule, Remark, RemarkSubject, RemarkMeasure, ExtraMeasure, SubjectTopic, MeasureTopic

import os, datetime, random
import unicodecsv  as  csv
import zipfile


def get_settings_and_show():
    settings = {}
    try:
        academic_year_list = db_schedule.db_schedule_academic_year_list()
        academic_year_list = academic_year_list if academic_year_list else [utils.academic_year()]
        last = academic_year_list[-1]
        academic_year_list.append(last + 101)
        topics = []
        measure_topics = db_measure_topic.db_measure_topic_list(all=True)
        mt_list = [{'id': i.id, 'enabled': i.enabled, 'topic': i.topic} for i in measure_topics]
        topics.append(('measure_topic', 'Maatregelen', mt_list))
        subject_topics = db_subject_topic.db_subject_topic_list(all=True)
        st_list = [{'id': i.id, 'enabled': i.enabled, 'topic': i.topic} for i in subject_topics]
        topics.append(('subject_topic', 'Opmerkingen', st_list))

        settings['sim_dayhour'] = db_setting.get_global_setting_sim_dayhour()
        settings['sim_dayhour_state'] = db_setting.get_global_setting_sim_dayhour_state()
    except Exception as e:
        log.error(u'Could not check the database for students or timetables, error {}'.format(e))
        utils.flash_plus(u'Er is een fout opgetreden bij het ophalen van de instellingen', e)

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
    elif request.form['save_subject'] == 'add_test_students':
        add_test_remarks()
    elif request.form['save_subject'] == 'delete_test_students':
        delete_test_remarks()
    elif request.form['save_subject'] == 'delete_schedule':
        delete_schedule()
    elif 'txt_sim_dayhour' in request.form:
        save_sim_dayhour()
    return redirect(url_for('settings.show'))


def save_sim_dayhour():
    try:
        db_setting.set_global_setting_sim_dayhour_state('chkb_sim_dayhour' in request.form)
        db_setting.set_global_setting_sim_dayhour(request.form['txt_sim_dayhour'])
    except Exception as e:
        log.error(u'Cannot save simulate dayhour: {}'.format(e))
        utils.flash_plus(u'Kan simulatie dag en uur niet bewaren', e)
    return


# NO PHOTOS ARE REMOVED, PHOTOS ARE ADDED ONLY
# upload and unzip a zipfile with photos
# if the same zipfile is uploaded with MORE photos then the additional photos are just added
# if the same zipfile is uploaded with LESS photos then NO photos are removed
def upload_photos(rfile):
    try:
        log.info('Upload photos from : {}'.format(rfile))
        # students_file=csv.DictReader(request.files['import_filename'],  delimiter=';', encoding='utf-8-sig')
        filename = documents.get_doc_reference('photo').save(rfile, name=rfile.filename)
        zip_file = os.path.join(documents.get_doc_path('photo'), filename)
        zip_ref = zipfile.ZipFile(zip_file, 'r')
        zip_ref.extractall(documents.get_doc_path('photo'))
        zip_ref.close()
        log.info(u'Uploaded photos')
        utils.flash_plus(u'Foto\'s zijn geïmporteerd')
    except Exception as e:
        log.error(u'Cannot import photos : {}'.format(e))
        utils.flash_plus(u'Kan bestand niet importeren', e)
    return


# NAAM           last_name
# VOORNAAM       first_name
# LEERLINGNUMMER number
# FOTO           photo
# KLAS           grade_id

# NO STUDENTS ARE REMOVED, STUDENTS ARE ADDED ONLY
# students are identified by an unique studentnumber
# if a list is uploaded again then it is checked if a student with the same studentnumber is already present
# if so,  update grade, photo and academic year

# Students whom go to another internal school (from lyceuem to instituut), are automatically put in the correct school.

# Students whom go to an external school or are finished stay in the database.

def upload_students(rfile):
    try:
        # format csv file :
        log.info(u'Import students from : {}'.format(rfile))

        # students_file=csv.DictReader(rfile, delimiter=';', encoding='utf-8-sig') #utf-8 encoding
        students_file = csv.DictReader(rfile, delimiter=';', encoding='latin_1')  # ansi encoding

        nbr_students = 0
        academic_year = request.form['selected_academic_year']
        grades = {g.code: g for g in db_grade.db_grade_list(academic_year=academic_year)}

        if grades:
            for s in students_file:
                # skip empy records
                if s['VOORNAAM'] != '' and s['NAAM'] != '' and s['LEERLINGNUMMER'] != '' and s['FOTO'] != '':
                    # check for grade.  If it not exists, skip
                    if s['KLAS'] in grades:
                        # add student, if not already present
                        find_student = Student.query.filter(Student.number == int(s['LEERLINGNUMMER'])).first()
                        if find_student:
                            find_student.photo = s['FOTO']
                            find_student.grade = grades[s['KLAS']]
                            find_student.academic_year = academic_year
                        else:
                            student = Student(first_name=s['VOORNAAM'], last_name=s['NAAM'], number=int(s['LEERLINGNUMMER']),
                                              photo=s['FOTO'], grade=grades[s['KLAS']], academic_year=academic_year)
                            db.session.add(student)
                            nbr_students += 1
            db.session.commit()
        else:
            log.error('Error, no grades present yet')
            utils.flash_plus('Fout, er zijn nog geen klassen ingeladen')

        log.info(u'import: added {} students'.format(nbr_students))
        utils.flash_plus(u'{} leerlingen zijn geïmporteerd'.format(nbr_students))

    except Exception as e:
        utils.flash_plus(u'Kan bestand niet importeren', e)
        log.error(u'cannot import : {}'.format(e))
    return


# FAMILIENAAM    last_name
# VOORNAAM       first_name
# CODE           code

# NO TEACHERS ARE REMOVED, TEACHERS ARE ADDED ONLY
def upload_teachers(rfile):
    try:
        # format csv file :
        log.info(u'Import teachers from : {}'.format(rfile))
        academic_year = request.form['selected_academic_year']
        # teachers_file=csv.DictReader(rfile,  delimiter=';', encoding='utf-8-sig')
        teachers_file = csv.DictReader(rfile, delimiter=';', encoding='latin_1')  # ansi encoding
        nbr_teachers = 0
        for t in teachers_file:
            # skip empy records
            if t['VOORNAAM'] != '' and t['FAMILIENAAM'] != '' and t['CODE'] != '':
                # add teacher, if not already present
                find_teacher = Teacher.query.filter(Teacher.code == t['CODE']).first()
                if find_teacher:
                    find_teacher.first_name = t['VOORNAAM']
                    find_teacher.last_name = t['FAMILIENAAM']
                    find_teacher.academic_year = academic_year
                if not find_teacher:
                    teacher = Teacher(first_name=t['VOORNAAM'], last_name=t['FAMILIENAAM'], code=t['CODE'], academic_year=academic_year)
                    db.session.add(teacher)
                    nbr_teachers += 1

        db.session.commit()
        log.info(u'import: added {} teachers'.format(nbr_teachers))
        utils.flash_plus(u'{} leerkrachten zijn geïmporteerd'.format(nbr_teachers))

    except Exception as e:
        utils.flash_plus(u'Kan bestand niet importeren', e)
    return


# VOLGNUMMER
# KLAS           Classgroup.code
# LEERKRACHT     Teacher.code
# VAK            Lesson.code
# LOKAAL
# DAG            Classmoment.day
# UUR            Classmoment.hour

# REMOVE OLD SCHEDULE AND UPLOAD NEW SCHEDULE
# if a grade does not exist yet, add it
# if a lesson does not exist yet, add it
def upload_schedule(rfile):
    try:
        # format csv file :
        log.info(u'Import timetable from : {}'.format(rfile))
        academic_year = request.form['selected_academic_year']

        # first, delete current timetable
        delete_classmoments(academic_year)

        fieldnames = ['VOLGNUMMER', 'KLAS', 'LEERKRACHT', 'VAK', 'LOKAAL', 'DAG', 'UUR']
        timetable_file = csv.DictReader(rfile, fieldnames=fieldnames, delimiter=',', encoding='utf-8-sig')
        nbr_classmoments = 0
        nbr_lessons = 0
        error_message = ''
        nbr_grades = 0
        grades = {g.code: g for g in db_grade.db_grade_list()}
        lessons = {l.code: l for l in db_lesson.db_lesson_list()}

        for t in timetable_file:
            # skip empy records
            if t['KLAS'] != '' and t['LEERKRACHT'] != '' and t['VAK'] != '' and t['DAG'] != '' and t['UUR'] != '':
                find_teacher = Teacher.query.filter(Teacher.code == t['LEERKRACHT']).first()
                if find_teacher:
                    grade_code = t['KLAS'][:2]  # leave out the grade
                    lesson_code = t['VAK']
                    # check for grade.  If it not exists, add it first
                    if grade_code in grades:
                        find_grade = grades[grade_code]
                    else:
                        find_grade = Grade(code=grade_code, school=utils.school())
                        db.session.add(find_grade)
                        grades[grade_code] = find_grade
                        nbr_grades += 1
                    # add lesson, if not already present
                    if lesson_code in lessons:
                        find_lesson = lessons[lesson_code]
                    else:
                        find_lesson = Lesson(code=lesson_code, school=utils.school())
                        db.session.add(find_lesson)
                        lessons[lesson_code] = find_lesson
                        nbr_lessons += 1
                    find_classmoment = Schedule.query.filter(Schedule.day == int(t['DAG']), Schedule.hour == int(t['UUR']),
                                                             Schedule.grade == find_grade, Schedule.teacher == find_teacher,
                                                             Schedule.lesson == find_lesson,
                                                             Schedule.school == utils.school(), Schedule.academic_year == utils.academic_year()).first()
                    if not find_classmoment:
                        classmoment = Schedule(day=int(t['DAG']), hour=int(t['UUR']),
                                               grade=find_grade, teacher=find_teacher, lesson=find_lesson,
                                               school=utils.school(), academic_year=utils.academic_year())
                        db.session.add(classmoment)
                        nbr_classmoments += 1
                else:
                    log.info(u'import timetable: teacher not found: {}'.format(t['LEERKRACHT']))
                    error_message += u'{} : niet gevonden<br>'.format(t['LEERKRACHT'])

        db.session.commit()
        log.info(u'import: added {} classmoments, {} grades and {} lessons'.format(nbr_classmoments, nbr_grades, nbr_lessons))
        if error_message == '':
            utils.flash_plus(u'Lesrooster is geïmporteerd, {} lestijden, {} klassen en {} lessen toegevoegd'.format(nbr_classmoments, nbr_grades, nbr_lessons))
        else:
            utils.flash_plus(u'Lesrooster kan niet worden geïmporteerd', format(error_message))

    except Exception as e:
        utils.flash_plus(u'Kan bestand niet importeren', e)
    return


def delete_classmoments(academic_year):
    classmoments = Schedule.query.filter(Schedule.school == utils.school(), Schedule.academic_year == academic_year).all()
    for c in classmoments:
        db.session.delete(c)
    db.session.commit()


def delete_schedule():
    academic_year = request.form['selected_academic_year']
    try:
        delete_classmoments(request.form['selected_academic_year'])
        log.info(u'Deleted timetable')
        utils.flash_plus(u'Lesrooster van jaar {} is gewist'.format(academic_year))
    except Exception as e:
        log.error(u'Could not not delete classmoments from {}, error {}'.format(academic_year, e))
        utils.flash_plus(u'Kan lesrooster van jaar {} niet wissen'.format(academic_year), e)
    return redirect(url_for('settings.show'))


remark_dates = [
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '1/3', '13/3', '15/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '1/3', '13/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '13/3', '15/3', '19/3', '21/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '1/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '1/3', '2/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '9/2', '10/2', '11/3', '19/3', '21/3'],
    ['5/1', '15/1', '16/1', '22/1', '24/1', '8/2', '10/2', '15/2', '16/2', '23/3', '27/3'],
]


def add_test_remarks():
    academic_year = request.form['selected_academic_year']
    nbr_test_students = int(request.form['nbr-test-students'])
    add_extra_measure = 'chkb-extra-measure' in request.form
    random.seed()
    try:
        classmoments = Schedule.query.join(Grade, Lesson, Teacher).filter(Schedule.school == utils.school(), Schedule.academic_year == utils.academic_year()) \
            .all()
        students = Student.query.join(Grade, Schedule).filter(Schedule.school == utils.school(), Schedule.academic_year == utils.academic_year()).all()

        for i in range(nbr_test_students):
            student = random.choice(students)
            dates = remark_dates[i % len(remark_dates)]
            for d in dates:
                classmoment = random.choice(classmoments)
                h = random.randint(10, 16)
                m = random.randint(1, 50)
                timestamp = datetime.datetime.strptime('{}/20{} {}:{}'.format(d, academic_year[2:4], h, m), '%d/%m/%Y %H:%M')
                remark = Remark(student=student, grade=student.grade, timestamp=timestamp, lesson=classmoment.lesson, teacher=classmoment.teacher,
                                measure_note='', subject_note='TESTOPMERKING', school=utils.school(), academic_year=utils.academic_year(), test=True,
                                extra_attention=random.choice([True, False, False, False]))
                s = random.choice(db_subject_topic.db_subject_topic_list())
                m = random.choice(db_measure_topic.db_measure_topic_list())
                subject = RemarkSubject(topic=s, remark=remark)
                measure = RemarkMeasure(topic=m, remark=remark)
                db.session.add(subject)
                db.session.add(measure)
                db.session.add(remark)

        if add_extra_measure:
            matched_remarks, non_matched_remarks = db_remark.db_filter_remarks_to_be_reviewed(academic_year, test=True, commit=False)
            for s, rll in matched_remarks:
                for id, extra_measure, rl in rll:
                    rids = [i.id for i in rl]
                    db_remark.db_add_extra_measure(rids, 'TEST: extra sanctie voor {} {}'.format(s.first_name, s.last_name), commit=False)
        db_remark.db_tag_remarks_as_reviewed()
        log.info(u'Added test remarks')
        utils.flash_plus(u'Test opmerkingen toegevoegd voor jaar {} '.format(academic_year))
    except Exception as e:
        log.error(u'Could not add test remarks error {}'.format(e))
        utils.flash_plus(u'Kan test opmerkingen voor jaar {} niet toevoegen'.format(academic_year), e)
    return redirect(url_for('settings.show'))


def delete_test_remarks():
    academic_year = request.form['selected_academic_year']
    try:
        remarks = Remark.query.filter(Remark.school == utils.school(), Remark.academic_year == utils.academic_year(), Remark.test == True).all()
        for r in remarks:
            if r.extra_measure and r.first_remark:
                db.session.delete(r.extra_measure)
            db.session.delete(r)
        db.session.commit()
        log.info(u'Removed test remarks')
        utils.flash_plus(u'Test opmerkingen verwijderd voor jaar {} '.format(academic_year))
    except Exception as e:
        log.error(u'Could not delete test remarks error {}'.format(e))
        utils.flash_plus(u'Kan test opmerkingen voor jaar {} niet verwijderen'.format(academic_year), e)
    return redirect(url_for('settings.show'))


@settings.route('/settings/add_topic/<string:subject>/<string:topic>', methods=['GET', 'POST'])
@supervisor_required
@login_required
def add_topic(subject, topic):
    try:
        if subject == 'measure_topic':
            topic = MeasureTopic(topic=topic, school=utils.school())
        elif subject == 'subject_topic':
            topic = SubjectTopic(topic=topic, school=utils.school())
        db.session.add(topic)
        db.session.commit()
    except Exception as e:
        log.error(u'Could not add {}, topic {}: {}'.format(subject, topic, e))
        utils.flash_plus(u'Kan onderwerp niet toevoegen', e)
    return redirect(url_for('settings.show'))


@settings.route('/settings/set_topic_status/<string:data>', methods=['GET', 'POST'])
@supervisor_required
@login_required
def set_topic_status(data):
    try:
        jd = json.loads(data)
        ti = jd['id'].split('-')
        id = int(ti[1])
        if ti[0] == 'measure_topic':
            topic = MeasureTopic.query.get(int(ti[1]))
        elif ti[0] == 'subject_topic':
            topic = SubjectTopic.query.get(int(ti[1]))
        if topic:
            topic.enabled = jd['status']
        db.session.commit()
    except Exception as e:
        log.error('could not change the status')
        return jsonify({"status": False})

    return jsonify({"status": True})
