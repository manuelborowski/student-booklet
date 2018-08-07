# -*- coding: utf-8 -*-
# app/models.py

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager
from sqlalchemy import UniqueConstraint

class User(UserMixin, db.Model):
    # Ensures table will be named in plural and not in singular
    # as is the name of the model
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), index=True)
    username = db.Column(db.String(256), index=True, unique=True)
    first_name = db.Column(db.String(256), index=True)
    last_name = db.Column(db.String(256), index=True)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    settings = db.relationship('Settings', cascade='all, delete', backref='user', lazy='dynamic')

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
                'is_admin': self.is_admin}

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
    offences = db.relationship('Offence', cascade='all, delete', backref='student', lazy='dynamic')
    classgroup_id = db.Column(db.Integer, db.ForeignKey('classgroups.id', ondelete='CASCADE'))


    # def __repr__(self):
    #     return '<Asset: {}>'.format(self.name)
    #
    # def log(self):
    #     return '<Asset: {}/{}/{}/{}/{}>'.format(self.id, self.name, self.qr_code, self.purchase.since, self.purchase.value)
    #
    # def ret_dict(self):
    #     return {'id':self.id, 'name':self.name, 'qr_code':self.qr_code, 'status':self.status, 'location':self.location,
    #             'db_status':self.db_status,  'serial':self.serial, 'description':self.description,'purchase':self.purchase.ret_dict()}


class Classgroup(db.Model):
    __tablename__= 'classgroups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    students = db.relationship('Student', cascade='all, delete', backref='classgroup', lazy='dynamic')
    classmoments = db.relationship('Classmoment', cascade='all, delete', backref='classgroup', lazy='dynamic')

    # def __repr__(self):
    #     return '{} / {}'.format(self.since, self.value)
    #
    # def log(self):
    #     return '<Purchase: {}/{}/{}/{}/{}/{}>'.format(self.id, self.since, self.value, self.device.brand, self.device.type, self.supplier.name)
    #
    # def ret_dict(self):
    #     return {'id':self.id, 'since':self.since.strftime('%d-%m-%Y'), 'value':float(self.value), 'commissioning':self.commissioning,
    #             'supplier': self.supplier.ret_dict(), 'device':self.device.ret_dict()}

class Classmoment(db.Model):
    __tablename__ = 'classmoments'

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer)
    hour = db.Column(db.Integer)
    classgroup_id = db.Column(db.Integer, db.ForeignKey('classgroups.id', ondelete='CASCADE'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'))

    # def __repr__(self):
    #     return '{} / {}'.format(self.brand, self.type)
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

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    offences = db.relationship('Offence', cascade='all, delete', backref='lesson', lazy='dynamic')
    classmoments = db.relationship('Classmoment', cascade='all, delete', backref='lesson', lazy='dynamic')

    # def __repr__(self):
    #     return '{}'.format(self.name)
    #
    # def log(self):
    #     return '<Supplier: {}/{}>'.format(self.id, self.name)
    #
    # def ret_dict(self):
    #     return {'id':self.id, 'name':self.name, 'description':self.description}

class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    code = db.Column(db.String(256))
    offences = db.relationship('Offence', cascade='all, delete', backref='teacher', lazy='dynamic')
    classmoments = db.relationship('Classmoment', cascade='all, delete', backref='teacher', lazy='dynamic')

class Offence(db.Model):
    __tablename__ = 'offences'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(256))
    measure = db.Column(db.String(256))
    week = db.Column(db.Integer)
    day = db.Column(db.Integer)
    hour = db.Column(db.Integer)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))


