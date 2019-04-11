# -*- coding: utf-8 -*-
# app/models.py


from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func
from . import log, db, app

import cgi

@app.before_first_request
def at_start():
    SubjectTopic.add_default_values_if_empty()
    MeasureTopic.add_default_values_if_empty()

class User(UserMixin, db.Model):
    # Ensures table will be named in plural and not in singular
    # as is the name of the model
    __tablename__ = 'users'

    class USER_TYPE:
        LOCAL = 'local'
        OAUTH = 'oauth'

    @staticmethod
    def get_zipped_types():
        return list(zip(['local', 'oauth'], ['LOCAL', 'OAUTH']))

    class LEVEL:
        USER = 1
        SUPERVISOR = 3
        ADMIN = 5

        ls = ["GEBRUIKER", "BEGELEIDER", "ADMINISTRATOR"]

        @staticmethod
        def i2s(i):
            if i == 1:
                return User.LEVEL.ls[0]
            elif i == 3:
                return User.LEVEL.ls[1]
            if i == 5:
                return User.LEVEL.ls[2]

    @staticmethod
    def get_zipped_levels():
        return list(zip(["1", "3", "5"], User.LEVEL.ls))

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), index=True)
    username = db.Column(db.String(256), index=True)
    first_name = db.Column(db.String(256), index=True)
    last_name = db.Column(db.String(256), index=True)
    password_hash = db.Column(db.String(256))
    level = db.Column(db.Integer)
    user_type = db.Column(db.String(256))
    last_login = db.Column(db.DateTime())
    settings = db.relationship('Settings', cascade='all, delete', backref='user', lazy='dynamic')

    @property
    def is_local(self):
        return self.user_type == User.USER_TYPE.LOCAL

    @property
    def is_oauth(self):
        return self.user_type == User.USER_TYPE.OAUTH

    @property
    def is_at_least_user(self):
        return self.level >= User.LEVEL.USER

    @property
    def is_strict_user(self):
        return self.level == User.LEVEL.USER

    @property
    def is_at_least_supervisor(self):
        return self.level >= User.LEVEL.SUPERVISOR

    @property
    def is_at_least_admin(self):
        return self.level >= User.LEVEL.ADMIN

    @property
    def password(self):
        raise AttributeError('Paswoord kan je niet lezen.')

    @password.setter
    def password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        else:
            return True

    def __repr__(self):
        return '<User: {}>'.format(self.username)

    def log(self):
        return '<User: {}/{}>'.format(self.id, self.username)

    def ret_dict(self):
        return {'id':self.id, 'DT_RowId':self.id, 'email':self.email, 'username':self.username, 'first_name':self.first_name, 'last_name':self.last_name,
                'level': User.LEVEL.i2s(self.level), 'user_type': self.user_type, 'last_login': self.last_login, 'cb': ''}

    @staticmethod
    def format_data(db_list):
        out = []
        for i in db_list:
            em = i.ret_dict()
            out.append(em)
        return out

# Set up user_loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Settings(db.Model):
    __tablename__ = 'settings'

    class SETTING_TYPE:
        E_INT = 'INT'
        E_STRING = 'STRING'
        E_FLOAT = 'FLOAT'
        E_BOOL = 'BOOL'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    value = db.Column(db.String(256))
    type = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

    UniqueConstraint('name', 'user_id')

    def log(self):
        return '<Setting: {}/{}/{}/{}>'.format(self.id, self.name, self.value, self.type)


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    number = db.Column(db.Integer)
    photo = db.Column(db.String(256))
    schoolyear = db.Column(db.String(256))  #e.g. 1718, 1819
    remarks = db.relationship('Remark', cascade='all, delete', backref='student', lazy='dynamic')
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id', ondelete='CASCADE'))


    def nbr_of_remarks(self):
        return Remark.query.join(Student).filter(Student.id == self.id).count()

    def __repr__(self):
        return '<Student: {}/{}/{}>'.format(self.id, self.first_name, self.last_name)

    def ret_dict(self):
        return {'id':self.id, 'first_name':self.first_name, 'last_name': self.last_name, 'grade': self.grade.ret_dict(),
                'full_name': u'{} {}'.format(self.first_name, self.last_name),
                'number' : self.nbr_of_remarks}

class Grade(db.Model):
    __tablename__= 'grades'

    @staticmethod
    def get_choices_list():
        l = db.session.query(Grade.id, Grade.code).distinct(Grade.code).order_by(Grade.code).all()
        return l

    @staticmethod
    def get_choices_with_empty_list():
        return [(-1, '')] + Grade.get_choices_list()

    @staticmethod
    def get_all_grades_for_teacher(teacher):
        l = db.session.query(Grade.id, Grade.code).join(Schedule) \
            .join(Teacher).filter(Teacher.id == teacher.id).distinct(Grade.code).order_by(Grade.code).all()
        return l

    def get_choice(self):
        return(self.id, self.code)

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(256))
    students = db.relationship('Student', cascade='all, delete', backref='grade', lazy='dynamic')
    remarks = db.relationship('Remark', cascade='all, delete', backref='grade', lazy='dynamic')
    schedules = db.relationship('Schedule', cascade='all, delete', backref='grade', lazy='dynamic')

    def __repr__(self):
        return 'Grade: {}/{}'.format(self.id, self.code)

    def ret_dict(self):
         return {'id':self.id, 'code': self.code}

class Schedule(db.Model):
    __tablename__ = 'schedules'

    WEEK_DAYS = ['MA', 'DI', 'WO', 'DO', 'VR']

    @staticmethod
    def get_choices_day_hour():
        l = []
        day_count=1
        for d in Schedule.WEEK_DAYS:
            lh = 6 if d == 'WO' else 10
            for h in range(1,lh):
                l.append(('{}/{}'.format(day_count, h), '{} : {}'.format(d, h)))
            day_count += 1
        return l

    @staticmethod
    def get_all_schedules_for_teacher(teacher):
        l = db.session.query(Schedule.day, Schedule.hour).filter(Schedule.teacher == teacher).distinct().order_by(Schedule.day, Schedule.hour).all()
        ll = [('{}/{}'.format(d, h), '{} : {}'.format(Schedule.WEEK_DAYS[d-1], h)) for (d, h) in l]
        return ll

    def get_data_day_hour(self):
        return '{}/{}'.format(self.day, self.hour)

    @staticmethod
    def get_all_teachers():
        l = db.session.query(Schedule.teacher_id, Teacher.code).join(Teacher).distinct().order_by(Teacher.code).all()
        return l

    @staticmethod
    def get_all_grades():
        l = db.session.query(Schedule.grade_id, Grade.code).join(Grade).distinct().order_by(Grade.code).all()
        return l

    @staticmethod
    def decode_dayhour(dayhour):
        try:
            day_hour = dayhour.split('/')
            return int(day_hour[0]), int(day_hour[1]) #day, hour
        except Exception as e:
            return 1, 1

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer)
    hour = db.Column(db.Integer)
    schoolyear = db.Column(db.String(256))  #e.g. 1718, 1819
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id', ondelete='CASCADE'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'))

    def __repr__(self):
        return 'Schedule: {}/{}/{}/{}/{}/{}/{}'.format(self.id, self.day, self.hour, self.schoolyear, self.grade.code, self.teacher.code, self.lesson.code)

class Lesson(db.Model):
    __tablename__ = 'lessons'

    @staticmethod
    def get_choices_list():
        l = db.session.query(Lesson.id, Lesson.code).distinct(Lesson.code).order_by(Lesson.code).all()
        return l

    @staticmethod
    def get_all_lessons_for_teacher(teacher):
        l = db.session.query(Lesson.id, Lesson.code).join(Schedule) \
            .join(Teacher).filter(Teacher.id == teacher.id).distinct(Lesson.code).order_by(Lesson.code).all()
        return l

    def get_choice(self):
        return (self.id, self.code)

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(256), unique=True)
    remarks = db.relationship('Remark', cascade='all, delete', backref='lesson', lazy='dynamic')
    schedules = db.relationship('Schedule', cascade='all, delete', backref='lesson', lazy='dynamic')

    def __repr__(self):
        return 'Lesson: {}/{}'.format(self.id, self.code)

    def ret_dict(self):
        return {'id':self.id, 'code': self.code}

class Teacher(db.Model):
    __tablename__ = 'teachers'

    @staticmethod
    def get_choices_list():
        l = [i for i in db.session.query(Teacher.id, Teacher.code).distinct(Teacher.code).order_by(Teacher.code).all()]
        return l

    @staticmethod
    def get_choices_with_empty_list():
        return [(-1, '')] + Teacher.get_choices_list()

    def get_choice(self):
        return(self.id, self.code)

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    code = db.Column(db.String(256))
    remarks = db.relationship('Remark', cascade='all, delete', backref='teacher', lazy='dynamic')
    schedules = db.relationship('Schedule', cascade='all, delete', backref='teacher', lazy='dynamic')

    def __repr__(self):
        return 'Teacher: {}/{}'.format(self.id, self.code)

    def ret_dict(self):
        return {'id':self.id, 'code':self.code}

class ExtraMeasure(db.Model):
    __tablename__ = 'extra_measures'

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(1024), default='')
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    remarks = db.relationship('Remark', backref='extra_measure', lazy='dynamic')

    def get_remarks(self):
        ol = []
        for o in self.remarks:
            ol.append(o.ret_dict())
        return ol

    def ret_dict(self):
        return {'id':self.id, 'DT_RowId':self.id, 'note':cgi.escape(self.note), 'date':self.timestamp.strftime('%d-%m-%Y %H:%M')}

    @staticmethod
    def format_data(db_list):
        out = []
        for i in db_list:
            em = i.ExtraMeasure.ret_dict()
            em['remark'] = {'student': {'full_name': i.Student.first_name + ' ' + i.Student.last_name}, 'grade': {'code': i.Grade.code}}
            out.append(em)
        return out

# class Hub(db.Model):
#     __tablename__ = 'hub'
#     id = db.Column(db.Integer, primary_key=True)
#     school = db.Column(db.String(1024), default='Lyceum')
#     valid_from = db.Column(db.Date, default=None)
#     academic_year = db.Column(db.Integer, default=None)



class Remark(db.Model):
    __tablename__ = 'remarks'

    @staticmethod
    def reverse_date(date):
        return '-'.join(date.split('-')[::-1])

    id = db.Column(db.Integer, primary_key=True)
    subject_note = db.Column(db.String(1024), default='')
    measure_note = db.Column(db.String(1024), default='')
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    extra_attention = db.Column(db.Boolean, default=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id', ondelete='CASCADE'))
    subjects = db.relationship('RemarkSubject', cascade='all, delete', backref='remark', lazy='dynamic')
    measures = db.relationship('RemarkMeasure', cascade='all, delete', backref='remark', lazy='dynamic')

    reviewed = db.Column(db.Boolean, default=False)
    extra_measure_id = db.Column(db.Integer, db.ForeignKey('extra_measures.id'))

    #of a list of remarks, leading to an extra measure, only one remark will have first_remark set to true
    first_remark = db.Column(db.Boolean, default=False)

    test = db.Column(db.Boolean, default=False)

    def ret_subjects(self):
        l = ''
        for s in self.subjects:
            l += s.topic.topic
            l +=', '
        l += self.subject_note
        return l

    def ret_measures(self):
        l = ''
        for m in self.measures:
            l += m.topic.topic
            l +=', '
        if self.measure_note != '':
            l = l + self.measure_note + ', '
        return l

    def ret_extra_measure(self):
        return self.extra_measure.note if self.extra_measure_id else ''

    def row_color(self):
        if self.extra_attention:
            return 'lightsalmon'
        else:
            return ''

    def checkbox_required(self):
        user_check = self.teacher.code == current_user.username if current_user.is_strict_user else True
        return user_check and not self.reviewed


    def ret_dict(self):
        return {'id':self.id, 'DT_RowId':self.id, 'date':self.timestamp.strftime('%d-%m-%Y %H:%M'), 'measure_note': cgi.escape(self.measure_note),
                'subject_note': cgi.escape(self.subject_note), 'reviewed' : 'X' if self.reviewed else '',
                'subjects': self.ret_subjects(), 'measures': self.ret_measures(), 'extra_attention': self.extra_attention, 'overwrite_row_color': self.row_color()}

    def __repr__(self):
        return u'ID({}) TS({}) SDNT({})'.format(self.id, self.timestamp.strftime('%d-%m-%Y %H:%M'), self.student.first_name + ' ' + self.student.last_name)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def format_data(db_list):
        out = []
        for i in db_list:
            em = i.Remark.ret_dict()
            em['student'] = {'full_name': i.Student.first_name + ' ' + i.Student.last_name, 'number': i.Student.nbr_of_remarks()}
            em['grade'] = {'code': i.Grade.code}
            em['teacher'] = {'code': i.Teacher.code}
            em['lesson'] = {'code': i.Lesson.code}
            em['cb'] = "<input type='checkbox' class='cb_all' name='cb' value='{}'>".format(i.Remark.id, i.Remark.id) if i.Remark.checkbox_required else ''

            out.append(em)
        return out



class SubjectTopic(db.Model):
    __tablename__ = 'subject_topics'

    default_topics = [
        'Materiaal vergeten',
        'Praten',
        'Stoort de les',
        'Geen aandacht',
        'GSM gebruiken',
        'Taak niet gemaakt'
    ]

    @staticmethod
    def add_default_values_if_empty():
        find_topics = SubjectTopic.query.all()
        if not find_topics:
            log.info('SubjectTopic table is empty, adding default values')
            for t in SubjectTopic.default_topics:
                db.session.add(SubjectTopic(topic=t))
            db.session.commit()

    @staticmethod
    def get_choices_list():
        l = db.session.query(SubjectTopic.id, SubjectTopic.topic).filter(SubjectTopic.enabled==True).order_by(SubjectTopic.topic).all()
        return l

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(1024))
    enabled = db.Column(db.Boolean, default=True)
    subject = db.relationship('RemarkSubject', cascade='all', backref='topic', lazy='dynamic')


class RemarkSubject(db.Model):
    __tablename__ = 'remark_subjects'

    id = db.Column(db.Integer, primary_key=True)

    topic_id = db.Column(db.Integer, db.ForeignKey('subject_topics.id'))
    remark_id = db.Column(db.Integer, db.ForeignKey('remarks.id', ondelete='CASCADE'))


class MeasureTopic(db.Model):
    __tablename__ = 'measure_topics'

    default_topics = [
        'Taak maken',
        'GSM afgenomen',
        'Buiten gezet',
        'Taakstudie',
        'Andere plaats'
    ]

    @staticmethod
    def add_default_values_if_empty():
        find_topics = MeasureTopic.query.all()
        if not find_topics:
            log.info('MeasureTopic table is empty, adding default values')
            for t in MeasureTopic.default_topics:
                db.session.add(MeasureTopic(topic=t))
            db.session.commit()

    @staticmethod
    def get_choices_list():
        l = db.session.query(MeasureTopic.id, MeasureTopic.topic).filter(MeasureTopic.enabled==True).order_by(MeasureTopic.topic).all()
        return l

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(1024))
    enabled = db.Column(db.Boolean, default=True)
    measure = db.relationship('RemarkMeasure', cascade='all', backref='topic', lazy='dynamic')


class RemarkMeasure(db.Model):
    __tablename__ = 'remark_measures'

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('measure_topics.id'))
    remark_id = db.Column(db.Integer, db.ForeignKey('remarks.id', ondelete='CASCADE'))
