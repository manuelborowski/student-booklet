from flask import render_template, redirect, url_for, request, json, jsonify
from flask_login import login_required

from . import settings, forms
from app import db, log, admin_required, supervisor_required

from app.utils import utils, documents
from app.database import db_measure_topic, db_subject_topic, db_setting, db_grade, db_remark, db_schedule, db_lesson, db_utils, \
    db_teacher \
    , multiple_items, db_classgroup
from app.layout import tables_config
from app.database.models import Grade, Student, Teacher, Lesson, Schedule, Remark, RemarkSubject, RemarkMeasure, ExtraMeasure, \
    SubjectTopic, MeasureTopic \
    , SCHOOL, Classgroup

import os, datetime, random
import unicodecsv as csv
import zipfile


def get_settings_and_show():
    settings = {}
    try:
        academic_year_list = db_schedule.db_schedule_academic_year_list()
        academic_year_list = academic_year_list if academic_year_list else [db_utils.academic_year()]
        last = academic_year_list[-1]
        academic_year_list.append(last + 101)
        topics = []
        measure_topics = db_measure_topic.db_measure_topic_list(all=True)
        mt_list = [{'id': i.id, 'enabled': i.enabled, 'topic': i.topic} for i in measure_topics]
        topics.append(('measure_topic', 'Maatregelen', mt_list))
        subject_topics = db_subject_topic.db_subject_topic_list(all=True)
        st_list = [{'id': i.id, 'enabled': i.enabled, 'topic': i.topic} for i in subject_topics]
        topics.append(('subject_topic', 'Opmerkingen', st_list))

        sim_day_hour = db_setting.get_global_setting_sim_dayhour()
        settings['sim_day'] = sim_day_hour.split(' ')[0]
        settings['sim_hour'] = sim_day_hour.split(' ')[1]
        settings['sim_dayhour_state'] = db_setting.get_global_setting_sim_dayhour_state()
        settings['help_url'] = db_setting.get_global_setting_help_url()
    except Exception as e:
        log.error(u'Could not check the database for students or timetables, error {}'.format(e))
        utils.flash_plus(u'Er is een fout opgetreden bij het ophalen van de instellingen', e)

    return settings, academic_year_list, topics

    return render_template(u'settings/topics.html',
                           settings=settings,
                           academic_year_list=academic_year_list,
                           topics=topics,
                           title='settings')


@settings.route('/settings/topics', methods=['GET', 'POST'])
@supervisor_required
@login_required
def show_topics():
    settings, academic_year_list, topics = get_settings_and_show()
    return render_template(u'settings/topics.html',
                           settings=settings,
                           academic_year_list=academic_year_list,
                           topics=topics,
                           title='settings')


@settings.route('/settings/replacements', methods=['GET', 'POST'])
@supervisor_required
@login_required
def show_replacements():
    _filter, _filter_form, a, b, c = multiple_items.process_data(tables_config.tables_configuration['replacement'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config=tables_config.tables_configuration['replacement'])


@settings.route('/settings/replacements_data', methods=['GET', 'POST'])
@login_required
def replacement_data():
    ajax_table = multiple_items.prepare_data_for_html(tables_config.tables_configuration['replacement'])
    return ajax_table


@settings.route('/settings/replacement_add', methods=['GET', 'POST'])
@login_required
def replacement_add():
    try:
        if utils.button_save_pushed():  # second pass
            pass
        else:  # first pass
            form = forms.AddReplacementForm()
            return render_template('settings/replacement.html', form=form, title='Voeg een vervanger toe', role='add',
                                   subject='settings')

    except Exception as e:
        log.error(u'Could not add replacment {}'.format(e))
        utils.flash_plus(u'Kan vervanger niet toevoegen', e)
    return redirect(url_for('settings.show_replacements'))


@settings.route('/settings/database', methods=['GET', 'POST'])
@supervisor_required
@login_required
def show_database():
    settings, academic_year_list, topics = get_settings_and_show()
    return render_template(u'settings/database.html',
                           settings=settings,
                           academic_year_list=academic_year_list,
                           topics=topics,
                           title='settings')


@settings.route('/settings/tests', methods=['GET', 'POST'])
@supervisor_required
@login_required
def show_tests():
    settings, academic_year_list, topics = get_settings_and_show()
    return render_template(u'settings/tests.html',
                           settings=settings,
                           academic_year_list=academic_year_list,
                           topics=topics,
                           title='settings')

@settings.route('/settings/generic', methods=['GET', 'POST'])
@supervisor_required
@login_required
def show_generic():
    settings, academic_year_list, topics = get_settings_and_show()
    return render_template(u'settings/generic.html',
                           settings=settings,
                           academic_year_list=academic_year_list,
                           topics=topics,
                           title='generic')


@settings.route('/settings/save', methods=['GET', 'POST'])
@admin_required
@login_required
def save():
    if request.files:
        if 'upload_students' in request.files and request.files['upload_students'].filename != '':
            upload_students(request.files['upload_students'])
        elif 'upload_teachers' in request.files and request.files['upload_teachers'].filename != '':
            upload_teachers(request.files['upload_teachers'])
        elif 'upload_schedule' in request.files and request.files['upload_schedule'].filename != '':
            upload_schedule(request.files['upload_schedule'])
        elif 'upload_photos' in request.files and request.files['upload_photos'].filename != '':
            upload_photos(request.files['upload_photos'])
    elif request.form['save_subject'] == 'add_test_students':
        return add_test_remarks()
    elif request.form['save_subject'] == 'delete_test_students':
        return delete_test_remarks()
    elif request.form['save_subject'] == 'delete_schedule':
        return delete_schedule()
    elif request.form['save_subject'] == 'truncate-database':
        return truncate_database()
    elif 'txt-sim-day' in request.form:
        return save_sim_dayhour()
    elif 'txt-help-url' in request.form:
        return save_generic()
    return redirect(url_for('settings.show_database'))


def save_sim_dayhour():
    try:
        db_setting.set_global_setting_sim_dayhour_state('chkb-sim-dayhour' in request.form)
        db_setting.set_global_setting_sim_dayhour(request.form['txt-sim-day'] + ' ' + request.form['txt-sim-hour'])
    except Exception as e:
        log.error(u'Cannot save simulate dayhour: {}'.format(e))
        utils.flash_plus(u'Kan simulatie dag en uur niet bewaren', e)
    return redirect(url_for('settings.show_tests'))

def save_generic():
    try:
        db_setting.set_global_setting_help_url(request.form['txt-help-url'])
    except Exception as e:
        log.error(u'Cannot save help-website-url: {}'.format(e))
        utils.flash_plus(u'Kan de help website URL niet bewaren', e)
    return redirect(url_for('settings.show_generic'))


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
# KLASGROEP      classgroup

# NO STUDENTS ARE REMOVED, STUDENTS ARE ADDED ONLY
# students are identified by an unique studentnumber
# if a list is uploaded again then it is checked if a student with the same studentnumber is already present
# if so,  update classgroup, photo and academic year

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
        classgroups = {c.code: c for c in db_classgroup.db_classgroup_list()}

        if classgroups:
            for s in students_file:
                # skip empty records
                if s['VOORNAAM'] != '' and s['NAAM'] != '' and s['LEERLINGNUMMER'] != '':
                    # check for grade.  If it not exists, skip
                    if s['KLASGROEP'] in classgroups:
                        # add student, if not already present
                        find_student = Student.query.filter(Student.number == int(s['LEERLINGNUMMER'])).first()
                        if find_student:
                            find_student.photo = s['FOTO']
                            find_student.classgroup = classgroups[s['KLASGROEP']]
                            find_student.academic_year = academic_year
                        else:
                            student = Student(first_name=s['VOORNAAM'], last_name=s['NAAM'], number=int(s['LEERLINGNUMMER']),
                                              photo=s['FOTO'], classgroup=classgroups[s['KLASGROEP']], academic_year=academic_year)
                            db.session.add(student)
                            nbr_students += 1
            db.session.commit()
        else:
            log.error('Error, no classgroups present yet')
            utils.flash_plus('Fout, er zijn nog geen klassen ingeladen')

        log.info(u'import: added {} students'.format(nbr_students))
        utils.flash_plus(u'{} leerlingen zijn geïmporteerd'.format(nbr_students))

    except Exception as e:
        utils.flash_plus(u'Kan bestand niet importeren', e)
        log.error(u'cannot import : {}'.format(e))
    return


# CODE           code
# VOORNAAM       first_name
# FAMILIENAAM    last_name
# GROEP          LeerkrachtenInstituut, LeerkrachtenMiddenschool, LeerkrachtenLyceum

group_to_school = {
    'LeerkrachtenInstituut': SCHOOL.INSTITUUT,
    'LeerkrachtenMiddenschool': SCHOOL.MIDDENSCHOOL,
    'LeerkrachtenLyceum': SCHOOL.LYCEUM
}


# NO TEACHERS ARE REMOVED, TEACHERS ARE ADDED ONLY
def upload_teachers(rfile):
    try:
        # format csv file :
        log.info(u'Import teachers from : {}'.format(rfile))
        academic_year = request.form['selected_academic_year']

        fieldnames = ['CODE', 'VOORNAAM', 'FAMILIENAAM', 'GROEP', 'GROEP2']
        # teachers_file=csv.DictReader(rfile,  delimiter=';', encoding='utf-8-sig')
        teachers_file = csv.DictReader(rfile, delimiter=';', fieldnames=fieldnames, encoding='latin_1')  # ansi encoding
        nbr_teachers = 0
        for t in teachers_file:
            # skip empty and not relevant records
            teacher_code = t['CODE'].upper()
            group = t['GROEP'] if t['GROEP'] in group_to_school else t['GROEP2']
            if group not in group_to_school: continue
            if t['VOORNAAM'] != '' and t['FAMILIENAAM'] != '' and teacher_code != '':
                school = group_to_school[group]
                # add teacher, if not already present
                find_teacher = Teacher.query.filter(Teacher.code == teacher_code, Teacher.school == school).first()
                if find_teacher:
                    find_teacher.first_name = t['VOORNAAM']
                    find_teacher.last_name = t['FAMILIENAAM']
                    find_teacher.academic_year = academic_year
                if not find_teacher:
                    teacher = Teacher(first_name=t['VOORNAAM'], last_name=t['FAMILIENAAM'], code=teacher_code,
                                      academic_year=academic_year, school=school)
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
# if a classgroup does not exist yeat, add it
# Store the selected academic year and valid-from-date
# A schedule is selected by the current academic year and the current date is equal to or later than the valid-from-date
def upload_schedule(rfile):
    try:
        # format csv file :
        log.info(u'Import timetable from : {}'.format(rfile))
        academic_year = request.form['selected_academic_year']
        valid_from = datetime.datetime.strptime(request.form['select-date-from'], '%d-%m-%Y')

        # first, delete current timetable
        delete_classmoments(academic_year, valid_from)

        fieldnames = ['VOLGNUMMER', 'KLAS', 'LEERKRACHT', 'VAK', 'LOKAAL', 'DAG', 'UUR']
        timetable_file = csv.DictReader(rfile, fieldnames=fieldnames, delimiter=',', encoding='utf-8-sig')
        nbr_classmoments = 0
        nbr_lessons = 0
        error_message = ''
        nbr_grades = 0
        nbr_classgroups = 0
        grades = {g.code: g for g in db_grade.db_grade_list(in_schedule=False)}
        classgroups = {c.code: c for c in db_classgroup.db_classgroup_list()}
        lessons = {l.code: l for l in db_lesson.db_lesson_list(schedule=False)}
        teachers = {t.code: t for t in db_teacher.db_teacher_list(schedule=False)}

        for t in timetable_file:
            # skip empy records
            if t['KLAS'] != '' and t['LEERKRACHT'] != '' and t['VAK'] != '' and t['DAG'] != '' and t['UUR'] != '':
                if t['LEERKRACHT'] in teachers:
                    find_teacher = teachers[t['LEERKRACHT']]
                    classgroup_code = t['KLAS']
                    if len(classgroup_code.split(' ')) == 1:
                        grade_code = classgroup_code
                    else:
                        grade_code = classgroup_code.split(' ')[0]
                    lesson_code = t['VAK']
                    # check for grade.  If it not exists, add it first
                    if grade_code in grades:
                        find_grade = grades[grade_code]
                    else:
                        find_grade = Grade(code=grade_code, school=db_utils.school())
                        db.session.add(find_grade)
                        grades[grade_code] = find_grade
                        nbr_grades += 1
                    # check for classgroup, if not present, add
                    if classgroup_code in classgroups:
                        find_classgroup = classgroups[classgroup_code]
                    else:
                        find_classgroup = Classgroup(code=classgroup_code, grade=find_grade)
                        db.session.add(find_classgroup)
                        classgroups[classgroup_code] = find_classgroup
                        nbr_classgroups += 1
                    # add lesson, if not already present
                    if lesson_code in lessons:
                        find_lesson = lessons[lesson_code]
                    else:
                        find_lesson = Lesson(code=lesson_code, school=db_utils.school())
                        db.session.add(find_lesson)
                        lessons[lesson_code] = find_lesson
                        nbr_lessons += 1
                    classmoment = Schedule(day=int(t['DAG']), hour=int(t['UUR']),
                                           classgroup=find_classgroup, teacher=find_teacher, lesson=find_lesson,
                                           school=db_utils.school()
                                           , academic_year=int(academic_year), valid_from=valid_from)
                    db.session.add(classmoment)
                    nbr_classmoments += 1
                else:
                    log.info(u'import timetable: teacher not found: {}'.format(t['LEERKRACHT']))
                    error_message += u'{} : niet gevonden<br>'.format(t['LEERKRACHT'])

        # load schedule for teacher XXXX
        period = day = 1
        teacher = db_teacher.db_teacher(code='XXXX')
        lesson = db_lesson.db_lesson_list()[0]
        for g in db_grade.db_grade_list():
            classgroups = db_classgroup.db_classgroup_list(grade=g)
            for cg in classgroups:
                classmoment = Schedule(day=day, hour=period, classgroup=cg, teacher=teacher, lesson=lesson,
                                       school=db_utils.school(), academic_year=int(academic_year), valid_from=valid_from)
                db.session.add(classmoment)
            period += 1
            if period > 9:
                period = 1
                day += 1
        db.session.commit()
        log.info(u'import: added {} classmoments, {} grades, {} classgroups and {} lessons'.format(nbr_classmoments, nbr_grades,
                                                                                                   nbr_classgroups, nbr_lessons))
        if error_message == '':
            utils.flash_plus(u'Lesrooster is geïmporteerd, {} lestijden, {} klassen, {} klasgroepen en {} lessen toegevoegd'.format(
                nbr_classmoments,
                nbr_grades, nbr_classgroups, nbr_lessons))
        else:
            utils.flash_plus(u'Lesrooster kan niet worden geïmporteerd', format(error_message))

    except Exception as e:
        utils.flash_plus(u'Kan bestand niet importeren', e)
    return


def delete_classmoments(academic_year, valid_from):
    classmoments = Schedule.query.filter(Schedule.academic_year == academic_year, Schedule.school == db_utils.school(),
                                         Schedule.valid_from == valid_from).all()
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
    return redirect(url_for('settings.show_database'))


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
        classmoments = db_schedule.query_filter(Schedule.query.join(Classgroup, Grade, Lesson, Teacher)).all()
        students = db_schedule.query_filter(Student.query.join(Classgroup, Grade, Schedule)).all()

        for i in range(nbr_test_students):
            student = random.choice(students)
            dates = remark_dates[i % len(remark_dates)]
            for d in dates:
                classmoment = random.choice(classmoments)
                h = random.randint(1, 9)
                timestamp = datetime.datetime.strptime('{}/20{} {}:{}:{}'.format(d, academic_year[2:4], 23, 59, h),
                                                       '%d/%m/%Y %H:%M:%S')
                remark = Remark(student=student, grade=student.classgroup.grade, timestamp=timestamp, lesson=classmoment.lesson,
                                teacher=classmoment.teacher,
                                measure_note='', subject_note='TESTOPMERKING', school=db_utils.school(),
                                academic_year=db_utils.academic_year(), test=True,
                                extra_attention=random.choice([True, False, False, False]))
                s = random.choice(db_subject_topic.db_subject_topic_list())
                m = random.choice(db_measure_topic.db_measure_topic_list())
                subject = RemarkSubject(topic=s, remark=remark)
                measure = RemarkMeasure(topic=m, remark=remark)
                db.session.add(subject)
                db.session.add(measure)
                db.session.add(remark)

        if add_extra_measure:
            matched_remarks, non_matched_remarks = db_remark.db_filter_remarks_to_be_reviewed(academic_year, test=True,
                                                                                              commit=False)
            for s, rll in matched_remarks:
                for id, extra_measure, rl in rll:
                    rids = [i.id for i in rl]
                    db_remark.db_add_extra_measure(rids, 'TEST: extra sanctie voor {} {}'.format(s.first_name, s.last_name),
                                                   commit=False)
        db_remark.db_tag_remarks_as_reviewed()
        log.info(u'Added test remarks')
        utils.flash_plus(u'Test opmerkingen toegevoegd voor jaar {} '.format(academic_year))
    except Exception as e:
        log.error(u'Could not add test remarks error {}'.format(e))
        utils.flash_plus(u'Kan test opmerkingen voor jaar {} niet toevoegen'.format(academic_year), e)
    return redirect(url_for('settings.show_tests'))


def delete_test_remarks():
    academic_year = request.form['selected_academic_year']
    try:
        remarks = Remark.query.filter(Remark.school == db_utils.school(), Remark.academic_year == db_utils.academic_year(),
                                      Remark.test == True).all()
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
    return redirect(url_for('settings.show_tests'))


@settings.route('/settings/add_topic/<string:subject>/<string:topic>', methods=['GET', 'POST'])
@supervisor_required
@login_required
def add_topic(subject, topic):
    try:
        if subject == 'measure_topic':
            topic = MeasureTopic(topic=topic, school=db_utils.school())
        elif subject == 'subject_topic':
            topic = SubjectTopic(topic=topic, school=db_utils.school())
        db.session.add(topic)
        db.session.commit()
    except Exception as e:
        log.error(u'Could not add {}, topic {}: {}'.format(subject, topic, e))
        utils.flash_plus(u'Kan onderwerp niet toevoegen', e)
    return redirect(url_for('settings.show_topics'))


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


def truncate_database():
    try:
        grades = Grade.query.all()
        for g in grades:
            db.session.delete(g)
        lessons = Lesson.query.all()
        for l in lessons:
            db.session.delete(l)
        teachers = Teacher.query.all()
        for t in teachers:
            db.session.delete(t)
        for mt in MeasureTopic.query.all():
            db.session.delete(mt)
        for st in SubjectTopic.query.all():
            db.session.delete(st)
        db.session.commit()
        log.info('Database truncated')
        utils.flash_plus('Database is gewist')
    except Exception as e:
        log.error('Could not truncate database: error {}'.format(e))
        utils.flash_plus('Kan database niet wissen', e)
    return redirect(url_for('settings.show_tests'))


@settings.route('/settings/action', methods=['GET', 'POST'])
@login_required
@admin_required
def action():
    if utils.button_pressed('add'):
        return add_replacement()
    return redirect(url_for('settings.show_replacements'))


@settings.route('/settings/action_done/<string:action>/<int:id>', methods=['GET', 'POST'])
@settings.route('/settings/action_done/<string:action>', methods=['GET', 'POST'])
@login_required
@admin_required
def action_done(action=None, id=-1):
    return redirect(url_for('settings.show_replacements'))


def add_replacement():
    pass
