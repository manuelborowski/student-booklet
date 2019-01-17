# -*- coding: utf-8 -*-
# app/models.py

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func

class User(UserMixin, db.Model):
    # Ensures table will be named in plural and not in singular
    # as is the name of the model
    __tablename__ = 'users'

    class USER_TYPE:
        LOCAL = 'local'
        OAUTH = 'oauth'

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
        return zip(["1", "3", "5"], User.LEVEL.ls)

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), index=True)
    username = db.Column(db.String(256), index=True, unique=True)
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
    def is_user(self):
        return self.level >= User.LEVEL.USER

    @property
    def is_strict_user(self):
        return self.level == User.LEVEL.USER

    @property
    def is_supervisor(self):
        return self.level >= User.LEVEL.SUPERVISOR

    @property
    def is_admin(self):
        return self.level >= User.LEVEL.ADMIN

    @property
    def password(self):
        """
        Prevent pasword from being accessed
        """
        raise AttributeError('Paswoord kan je niet lezen.')

    @password.setter
    def password(self, password):
        """
        Set password to a hashed password
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """
        Check if hashed password matches actual password
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User: {}>'.format(self.username)

    def log(self):
        return '<User: {}/{}>'.format(self.id, self.username)

    def ret_dict(self):
        return {'id':self.id, 'email':self.email, 'username':self.username, 'first_name':self.first_name, 'last_name':self.last_name,
                'level': User.LEVEL.i2s(self.level), 'user_type': self.user_type, 'last_login': self.last_login, 'cb': ''}

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
    offences = db.relationship('Offence', cascade='all, delete', backref='student', lazy='dynamic')
    classgroup_id = db.Column(db.Integer, db.ForeignKey('classgroups.id', ondelete='CASCADE'))


    def __repr__(self):
        return '<Student: {}/{}/{}>'.format(self.id, self.first_name, self.last_name)

    def ret_dict(self):
        return {'id':self.id, 'first_name':self.first_name, 'last_name': self.last_name, 'classgroup': self.classgroup.ret_dict(),
                'full_name': u'{} {}'.format(self.first_name, self.last_name),
                'number' : Offence.query.join(Student).filter(Student.id == self.id).count()}

    # def log(self):
    #     return '<Asset: {}/{}/{}/{}/{}>'.format(self.id, self.name, self.qr_code, self.purchase.since, self.purchase.value)
    #
    # def ret_dict(self):
    #     return {'id':self.id, 'name':self.name, 'qr_code':self.qr_code, 'status':self.status, 'location':self.location,
    #             'db_status':self.db_status,  'serial':self.serial, 'description':self.description,'purchase':self.purchase.ret_dict()}

class Classgroup(db.Model):
    __tablename__= 'classgroups'

    @staticmethod
    def get_choices_list():
        l = [i for i in db.session.query(Classgroup.id, Classgroup.name).distinct(Classgroup.name).order_by(Classgroup.name).all()]
        return l

    @staticmethod
    def get_choices_with_empty_list():
        return [(0, '')] + Classgroup.get_choices_list()

    @staticmethod
    def get_choices_filtered_by_teacher_list(teacher):
        l = [i for i in db.session.query(Classgroup.id, Classgroup.name).join(Classmoment) \
            .join(Teacher).filter(Teacher.id == teacher.id).distinct(Classgroup.name).order_by(Classgroup.name).all()]
        return l

    def get_choice(self):
        return(self.id, self.name)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    students = db.relationship('Student', cascade='all, delete', backref='classgroup', lazy='dynamic')
    offences = db.relationship('Offence', cascade='all, delete', backref='classgroup', lazy='dynamic')
    classmoments = db.relationship('Classmoment', cascade='all, delete', backref='classgroup', lazy='dynamic')

    def __repr__(self):
        return 'Classgroup: {}/{}'.format(self.id, self.name)
    #
    # def log(self):
    #     return '<Purchase: {}/{}/{}/{}/{}/{}>'.format(self.id, self.since, self.value, self.device.brand, self.device.type, self.supplier.name)
    #
    def ret_dict(self):
         return {'id':self.id, 'name': self.name}

class Classmoment(db.Model):
    __tablename__ = 'classmoments'

    WEEK_DAYS = ['MA', 'DI', 'WO', 'DO', 'VR']

    @staticmethod
    def get_choices_day_hour():
        l = []
        day_count=1
        for d in Classmoment.WEEK_DAYS:
            lh = 6 if d == 'WO' else 10
            for h in range(1,lh):
                l.append(('{}/{}'.format(day_count, h), '{} : {}'.format(d, h)))
            day_count += 1
        return l

    def get_data_day_hour(self):
        return '{}/{}'.format(self.day, self.hour)

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
    classgroup_id = db.Column(db.Integer, db.ForeignKey('classgroups.id', ondelete='CASCADE'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'))

    def __repr__(self):
        return 'Classmoment: {}/{}/{}/{}/{}/{}/{}'.format(self.id, self.day, self.hour, self.schoolyear, self.classgroup.name, self.teacher.code, self.lesson.name)
    #
    # def log(self):
    #     return '<Device: {}/{}/{}>'.format(self.id, self.brand, self.type)
    #
    # def ret_dict(self):
    #     return {'id':self.id, 'brand':self.brand, 'type':self.type, 'category':self.category, 'power':float(self.power), 'photo':self.photo,
    #     'risk_analysis': self.risk_analysis, 'manual':self.manual, 'safety_information':self.safety_information, 'ce':self.ce,
    #     'brandtype':self.brand + ' / ' + self.type}

class Lesson(db.Model):
    __tablename__ = 'lessons'

    @staticmethod
    def get_choices_list():
        l = [i for i in db.session.query(Lesson.id, Lesson.name).distinct(Lesson.name).order_by(Lesson.name).all()]
        return l

    @staticmethod
    def get_choices_filtered_by_teacher_list(teacher):
        l = [i for i in db.session.query(Lesson.id, Lesson.name).join(Classmoment) \
            .join(Teacher).filter(Teacher.id == teacher.id).distinct(Lesson.name).order_by(Lesson.name).all()]
        return l

    def get_choice(self):
        return (self.id, self.name)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    offences = db.relationship('Offence', cascade='all, delete', backref='lesson', lazy='dynamic')
    classmoments = db.relationship('Classmoment', cascade='all, delete', backref='lesson', lazy='dynamic')

    def __repr__(self):
        return 'Lesson: {}/{}'.format(self.id, self.name)

    def ret_dict(self):
        return {'id':self.id, 'name': self.name}
    #
    # def log(self):
    #     return '<Supplier: {}/{}>'.format(self.id, self.name)
    #
    # def ret_dict(self):
    #     return {'id':self.id, 'name':self.name, 'description':self.description}

class Teacher(db.Model):
    __tablename__ = 'teachers'

    @staticmethod
    def get_choices_list():
        l = [i for i in db.session.query(Teacher.id, Teacher.code).distinct(Teacher.code).order_by(Teacher.code).all()]
        return l

    @staticmethod
    def get_choices_with_empty_list():
        return [(0, '')] + Teacher.get_choices_list()

    def get_choice(self):
        return(self.id, self.code)

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    code = db.Column(db.String(256))
    offences = db.relationship('Offence', cascade='all, delete', backref='teacher', lazy='dynamic')
    classmoments = db.relationship('Classmoment', cascade='all, delete', backref='teacher', lazy='dynamic')

    def __repr__(self):
        return 'Teacher: {}/{}'.format(self.id, self.code)

    def ret_dict(self):
        return {'id':self.id, 'code':self.code}

class ExtraMeasure(db.Model):
    __tablename__ = 'extra_measures'

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(1024), default='')
    offences = db.relationship('Offence', backref='extra_measure', lazy='dynamic')

    def ret_dict(self):
        return {'id':self.id, 'note':self.note}


class Offence(db.Model):
    __tablename__ = 'offences'

    @staticmethod
    def reverse_date(date):
        return '-'.join(date.split('-')[::-1])

    id = db.Column(db.Integer, primary_key=True)
    type_note = db.Column(db.String(1024), default='')
    measure_note = db.Column(db.String(1024), default='')
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))
    classgroup_id = db.Column(db.Integer, db.ForeignKey('classgroups.id', ondelete='CASCADE'))
    types = db.relationship('Type', cascade='all, delete', backref='offence', lazy='dynamic')
    measures = db.relationship('Measure', cascade='all, delete', backref='offence', lazy='dynamic')

    reviewed = db.Column(db.Boolean, default=False)
    measure_id = db.Column(db.Integer, db.ForeignKey('extra_measures.id'))

    def ret_types(self):
        l = ''
        for t in self.types:
            l += Type.types[t.type]
            l +=', '
        l += self.type_note
        return l

    def ret_measures(self):
        l = ''
        for t in self.measures:
            l += Measure.measures[t.measure]
            l +=', '
        l += self.measure_note
        return l

    def ret_dict(self):
        return {'id':self.id, 'date':self.timestamp.strftime('%d-%m-%Y %H:%M'), 'measure_note': self.measure_note, 'type_note': self.type_note,
                'teacher':self.teacher.ret_dict(), 'classgroup': self.classgroup.ret_dict(), 'lesson': self.lesson.ret_dict(), 'cb': '',
                'types': self.ret_types(), 'measures': self.ret_measures(), 'student': self.student.ret_dict()}

    def __repr__(self):
        return u'ID({}) TS({}) SDNT({})'.format(self.id, self.timestamp.strftime('%d-%m-%Y %H:%M'), self.student.first_name + ' ' + self.student.last_name)

    def __str__(self):
        return self.__repr__()

class Type(db.Model):
    __tablename__ = 'offence_types'

    types = {
        0: 'Materiaal vergeten',
        1: 'Praten',
        2: 'Stoort de les',
        3: 'Geen aandacht',
        4: 'GSM gebruiken',
        5: 'Taak niet gemaakt'
    }

    #types_skip = (2, 4)
    types_skip = ()

    @staticmethod
    def get_choices_list():
        l = []
        for k, v in Type.types.iteritems():
            if k in Type.types_skip: continue
            l.append((k, v))
        return l

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer)
    offence_id = db.Column(db.Integer, db.ForeignKey('offences.id', ondelete='CASCADE'))


class Measure(db.Model):
    __tablename__ = 'offence_measures'

    measures =  {
        0: 'Taak maken',
        1: 'GSM afgenomen',
        2: 'Buiten gezet',
        3: 'Taakstudie',
        4: 'Andere plaats'
    }

    #measures_skip = (1, 2, 3)
    measures_skip = ()

    @staticmethod
    def get_choices_list():
        l = []
        for k, v in Measure.measures.iteritems():
            if k in Measure.measures_skip: continue
            l.append((k, v))
        return l

    id = db.Column(db.Integer, primary_key=True)
    measure = db.Column(db.Integer)
    offence_id = db.Column(db.Integer, db.ForeignKey('offences.id', ondelete='CASCADE'))
