from app import db
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import UniqueConstraint, select, event
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy.sql import func
from sqlalchemy.orm import column_property


# cascade delete : if a table is truncated, what tables are truncated as wel?
# Remark -> RemarkSubject, RemarkMeasure
# Lesson -> Remark, Schedule
# Teacher -> Remark, Schedule
# Student -> Remark
# Grade -> Student, Schedule

class SCHOOL:
    LYCEUM = 'Lyceum'
    MIDDENSCHOOL = 'Middenschool'
    INSTITUUT = 'Instituut'


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
        return {'id': self.id, 'DT_RowId': self.id, 'email': self.email, 'username': self.username, 'first_name': self.first_name,
                'last_name': self.last_name,
                'level': User.LEVEL.i2s(self.level), 'user_type': self.user_type, 'last_login': self.last_login, 'chbx': ''}

    @staticmethod
    def format_data(db_list):
        out = []
        for i in db_list:
            em = i.ret_dict()
            em['chbx'] = "<input type='checkbox' class='chbx_all' name='chbx' value='{}'>".format(i.id)
            out.append(em)
        return out


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
    hidden = db.Column(db.Boolean, default=False)
    remarks = db.relationship('Remark', cascade='all, delete', backref='student', lazy='dynamic')
    classgroup_id = db.Column(db.Integer, db.ForeignKey('classgroups.id', ondelete='CASCADE'))
    academic_year = db.Column(db.Integer, default=None)
    photoblob = db.Column(MEDIUMBLOB)
    # nbr_of_remarks is a function in the database
    nbr_of_remarks = column_property(func.nbr_of_remarks(id))
    full_name = column_property(func.full_name(id))

    def __repr__(self):
        return '<Student: {}/{}/{}>'.format(self.id, self.first_name, self.last_name)

    def ret_dict(self):
        return {'id': self.id, 'first_name': self.first_name, 'last_name': self.last_name, 'grade': self.grade.ret_dict(),
                'full_name': self.full_name,
                'number': self.nbr_of_remarks}


class Classgroup(db.Model):
    __tablename__ = 'classgroups'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(256))
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id', ondelete='CASCADE'))
    students = db.relationship('Student', cascade='all, delete', backref='classgroup', lazy='dynamic')
    schedules = db.relationship('Schedule', cascade='all, delete', backref='classgroup', lazy='dynamic')
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return '<Classgroup: {}/{}>'.format(self.id, self.code)


class Grade(db.Model):
    __tablename__ = 'grades'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(256))
    remarks = db.relationship('Remark', cascade='all, delete', backref='grade', lazy='dynamic')
    classgroups = db.relationship('Classgroup', cascade='all, delete', backref='grade', lazy='dynamic')
    school = db.Column(db.String(256))

    @staticmethod
    def get_choices_list():
        l = db.session.query(Grade.id, Grade.code).distinct(Grade.code).order_by(Grade.code).all()
        return l

    @staticmethod
    def get_choices_with_empty_list():
        return [(-1, '')] + Grade.get_choices_list()

    def get_choice(self):
        return (self.id, self.code)

    def __repr__(self):
        return 'Grade: {}/{}'.format(self.id, self.code)

    def ret_dict(self):
        return {'id': self.id, 'code': self.code}


class Schedule(db.Model):
    __tablename__ = 'schedules'

    WEEK_DAYS = ['MA', 'DI', 'WO', 'DO', 'VR']

    @staticmethod
    def get_choices_day_hour():
        l = []
        day_count = 1
        for d in Schedule.WEEK_DAYS:
            lh = 6 if d == 'WO' else 10
            for h in range(1, lh):
                l.append(('{}/{}'.format(day_count, h), '{} : {}'.format(d, h)))
            day_count += 1
        return l

    def get_data_day_hour(self):
        return '{}/{}'.format(self.day, self.hour)

    @staticmethod
    def decode_dayhour(dayhour):
        try:
            day_hour = dayhour.split('/')
            return int(day_hour[0]), int(day_hour[1])  # day, hour
        except Exception as e:
            return 1, 1

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer)
    hour = db.Column(db.Integer)
    classgroup_id = db.Column(db.Integer, db.ForeignKey('classgroups.id', ondelete='CASCADE'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'))
    school = db.Column(db.String(1024), default='Lyceum', index=True)
    valid_from = db.Column(db.Date, default=None, index=True)
    academic_year = db.Column(db.Integer, default=None, index=True)
    test = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return 'Schedule: {}/{}/{}/{}/{}/{}'.format(self.id, self.day, self.hour, self.classgroup.code, self.teacher.code,
                                                    self.lesson.code)


class Lesson(db.Model):
    __tablename__ = 'lessons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(256), unique=True)
    remarks = db.relationship('Remark', cascade='all, delete', backref='lesson', lazy='dynamic')
    schedules = db.relationship('Schedule', cascade='all, delete', backref='lesson', lazy='dynamic')
    school = db.Column(db.String(256), default='Lyceum')

    def get_choice(self):
        return (self.id, self.code)

    def __repr__(self):
        return 'Lesson: {}/{}'.format(self.id, self.code)

    def ret_dict(self):
        return {'id': self.id, 'code': self.code}


class ReplacementTeacher(db.Model):
    __tablename__ = 'replacement_teachers'

    id = db.Column(db.Integer, primary_key=True)
    replacing_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))
    replaced_by_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))
    school = db.Column(db.String(256), default='Lyceum')
    academic_year = db.Column(db.Integer, default=None)
    first_replacement_teacher = db.Column(db.Boolean, default=False)

    @staticmethod
    def format_data(db_list):
        out = []
        replacements = {}
        for i in db_list:
            if i.ReplacementTeacher.replaced_by_teacher in replacements:
                replacements[i.ReplacementTeacher.replaced_by_teacher].append(i.ReplacementTeacher.replacing_teacher)
            else:
                replacements[i.ReplacementTeacher.replaced_by_teacher] = [i.ReplacementTeacher.replacing_teacher]
        for k, v in replacements.items():
            em = {}
            em['replaced_by'] = '{} ({} {})'.format(k.code, k.first_name, k.last_name)
            l = ''
            for t in v:
                l += '{} ({} {})'.format(t.code, t.first_name, t.last_name) + ', '
            em['replacing'] = l
            em['chbx'] = "<input type='checkbox' class='chbx_all' name='chbx' value='{}'>".format(k.id)  # replaced-by-teacher-id
            out.append(em)
        return out


class Teacher(db.Model):
    __tablename__ = 'teachers'

    def get_choice(self):
        return (self.id, self.code)

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    code = db.Column(db.String(256))
    academic_year = db.Column(db.Integer, default=None)
    school = db.Column(db.String(256), default='Lyceum')
    hidden = db.Column(db.Boolean, default=False)
    remarks = db.relationship('Remark', cascade='all, delete', backref='teacher', lazy='dynamic')
    schedules = db.relationship('Schedule', cascade='all, delete', backref='teacher', lazy='dynamic')
    replacing_teacher = db.relationship('ReplacementTeacher', cascade='all', backref='replacing_teacher',
                                        foreign_keys='ReplacementTeacher.replacing_id', lazy='dynamic')
    replaced_by_teacher = db.relationship('ReplacementTeacher', cascade='all', backref='replaced_by_teacher',
                                          foreign_keys='ReplacementTeacher.replaced_by_id', lazy='dynamic')

    def __repr__(self):
        return 'Teacher: {}/{}'.format(self.id, self.code)

    def ret_dict(self):
        return {'id': self.id, 'code': self.code}

    @property
    def full(self):
        return '{} ({} {})'.format(self.code, self.first_name, self.last_name)


class Forward(db.Model):
    __tablename__ = 'forwards'

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(1024), default='')


class ExtraMeasure(db.Model):
    __tablename__ = 'extra_measures'

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(1024), default='')
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now())
    forward_to = db.Column(db.Integer, db.ForeignKey('users.id'), default=None)
    remarks = db.relationship('Remark', backref='extra_measure', lazy='dynamic')

    def ret_dict(self):
        return {'id': self.id, 'DT_RowId': self.id, 'note': self.note, 'date': self.timestamp.strftime('%d-%m-%Y %H:%M')}

    @staticmethod
    def format_data(db_list):
        out = []
        for i in db_list:
            em = i.ExtraMeasure.ret_dict()
            em['remark'] = {'student': {'full_name': i.Student.full_name}, 'grade': {'code': i.Grade.code}}
            out.append(em)
        return out


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
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'))  # child
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id', ondelete='CASCADE'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='CASCADE'))
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id', ondelete='CASCADE'))
    subjects = db.relationship('RemarkSubject', cascade='all, delete', backref='remark', lazy='dynamic')  # parent
    measures = db.relationship('RemarkMeasure', cascade='all, delete', backref='remark', lazy='dynamic')

    reviewed = db.Column(db.Boolean, default=False)
    extra_measure_id = db.Column(db.Integer, db.ForeignKey('extra_measures.id'))

    school = db.Column(db.String(256), default='Lyceum')
    academic_year = db.Column(db.Integer, default=None)
    test = db.Column(db.Boolean, default=False)

    # of a list of remarks, leading to an extra measure, only one remark will have first_remark set to true
    first_remark = db.Column(db.Boolean, default=False)

    # concat_remark_subjects and concat_remark_measures are functions in the database
    concat_subjects = column_property(func.concat_remark_subjects(id))
    concat_measures = column_property(func.concat_remark_measures(id))

    def row_color(self):
        if self.extra_attention:
            return 'lightsalmon'
        else:
            return ''

    def checkbox_required(self):
        user_check = self.teacher == current_user.teacher if current_user.is_strict_user else True
        return user_check and not self.reviewed

    def decode_timestamp(self):
        if self.timestamp.hour == 23 and self.timestamp.minute == 59:
            return '{} {}{} uur'.format(self.timestamp.strftime('%d-%m-%Y'), self.timestamp.second,
                                        'ste' if self.timestamp.second == 1 else 'de')
        return self.timestamp.strftime('%d-%m-%Y %H:%M')

    def ret_dict(self):
        return {'id': self.id, 'DT_RowId': self.id, 'date': self.decode_timestamp(), 'reviewed': 'X' if self.reviewed else '',
                'subjects': self.concat_subjects, 'measures': self.concat_measures, 'extra_attention': self.extra_attention,
                'overwrite_row_color': self.row_color()}

    def __repr__(self):
        return u'ID({}) TS({}) SDNT({})'.format(self.id, self.timestamp.strftime('%d-%m-%Y %H:%M'),
                                                self.student.first_name + ' ' + self.student.last_name)

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def format_data(db_list):
        out = []
        for i in db_list:
            em = i.Remark.ret_dict()
            em['student'] = {'full_name': i.Student.full_name, 'number': i.Student.nbr_of_remarks}
            em['grade'] = {'code': i.Grade.code}
            em['teacher'] = {'code': i.Teacher.code}
            em['lesson'] = {'code': i.Lesson.code}
            em['chbx'] = "<input type='checkbox' class='chbx_all' name='chbx' value='{}'>".format(i.Remark.id,
                                                                                                  i.Remark.id) if i.Remark.checkbox_required() else ''

            out.append(em)
        return out


class SubjectTopic(db.Model):
    __tablename__ = 'subject_topics'

    default_topics = [
        (SCHOOL.LYCEUM, [
            'gsm-gebruik',
            'Materiaal vergeten',
            'Neemt geen notities',
            'Stoort de les',
            'Taak of lesvoorbereiding niet gemaakt',
            'Voert opdrachten niet uit',
            'Volgt instructies niet op'
        ])
    ]

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(1024))
    enabled = db.Column(db.Boolean, default=True)
    subject = db.relationship('RemarkSubject', cascade='all', backref='topic', lazy='dynamic')
    school = db.Column(db.String(256), default='Lyceum')


class RemarkSubject(db.Model):
    __tablename__ = 'remark_subjects'

    id = db.Column(db.Integer, primary_key=True)

    topic_id = db.Column(db.Integer, db.ForeignKey('subject_topics.id'))
    remark_id = db.Column(db.Integer, db.ForeignKey('remarks.id', ondelete='CASCADE'))


class MeasureTopic(db.Model):
    __tablename__ = 'measure_topics'

    default_topics = [
        (SCHOOL.LYCEUM, [
            'Andere plaats gegeven',
            'gsm afgenomen',
            'Opmerking gegeven',
            'Uit de les gezet',
            'Werkstudie gegeven'
        ])
    ]

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(1024))
    enabled = db.Column(db.Boolean, default=True)
    measure = db.relationship('RemarkMeasure', cascade='all', backref='topic', lazy='dynamic')
    school = db.Column(db.String(256), default='Lyceum')

    @staticmethod
    def get_choices_list():
        l = db.session.query(MeasureTopic.id, MeasureTopic.topic).filter(MeasureTopic.enabled == True).order_by(
            MeasureTopic.topic).all()
        return l


class RemarkMeasure(db.Model):
    __tablename__ = 'remark_measures'

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('measure_topics.id'))
    remark_id = db.Column(db.Integer, db.ForeignKey('remarks.id', ondelete='CASCADE'))
