# -*- coding: utf-8 -*-

from app.database.models import User, Remark, Teacher, Student, Grade, Lesson, ExtraMeasure, ReplacementTeacher
from app.database.db_user import filter

tables_configuration = {
    'remark' : {
        'model' : Remark,
        'title' : 'Boekje',
        'subject' :'remarks',
        'buttons' : ['delete', 'edit', 'start_check'],
        'delete_message' : u'Wilt u deze opmerking(en) verwijderen?',
        'template' : [{'name': 'chbx', 'data':'chbx', 'order_by': Remark.timestamp, 'width': '1%', 'orderable' : False},
                      {'name': 'reviewed', 'data':'reviewed', 'order_by': Remark.reviewed, 'width': '1%', 'orderable' : True},
                      {'name': 'Datum', 'data':'date', 'order_by': Remark.timestamp, 'width': '10%', 'orderable' : True},
                      {'name': 'Leerling', 'data':'student.full_name', 'order_by': Student.last_name, 'width': '10%', 'orderable' : True},
                      {'name': '#', 'data':'student.number', 'order_by': lambda k: k['student']['number'], 'width': '1%', 'orderable' : True},
                      {'name': 'LKR', 'data':'teacher.code', 'order_by': Teacher.code, 'width': '1%', 'orderable' : True},
                      {'name': 'KL', 'data':'grade.code', 'order_by': Grade.code, 'width': '1%', 'orderable' : True},
                      {'name': 'Les', 'data':'lesson.code', 'order_by': Lesson.code, 'width': '5%', 'orderable' : True},
                      {'name': 'Opmerking', 'data':'subjects', 'order_by': lambda k: k['subjects'], 'width': '30%', 'orderable' : True},
                      {'name': 'Maatregel', 'data':'measures', 'order_by': lambda k: k['measures'], 'width': '30%', 'orderable' : True},
                      ],
        'data_endpoint': 'data',
        'filter' :  ['academic_year', 'teacher', 'grade', 'lesson', 'reviewed'],
        'href': [],
        'format_data': Remark.format_data,
        'legend': '<span class="badge legend-badge" style="background-color: lightsalmon">Extra aandacht</span>',
        'default_order' : (2, 'desc')
},
    'extra_measure' : {
        'model' : ExtraMeasure,
        'title' : 'Afgewerkt',
        'subject' :'reviewed',
        'delete_message' : u'Wilt u deze opmerking(en) verwijderen?',
        'template' : [
                      {'name': 'Datum', 'data':'date', 'order_by': ExtraMeasure.timestamp, 'width': '12%', 'orderable' : True},
                      {'name': 'Leerling', 'data':'remark.student.full_name', 'order_by': Student.last_name, 'width': '10%', 'orderable' : True},
                      {'name': 'KL', 'data':'remark.grade.code', 'order_by': Grade.code, 'width': '1%', 'orderable' : True},
                      {'name': 'Maatregel', 'data':'note', 'order_by': lambda k: k['note'], 'width': '30%', 'orderable' : True},
                      ],
        'data_endpoint' : 'data',
        'filter' :  ['academic_year', 'grade', 'lesson'],
        'href': [],
        'row_detail' : 'reviewed',
        'format_data' : ExtraMeasure.format_data,
        'legend': '<span class="badge legend-badge" style="background-color: lightsalmon">Extra aandacht</span>',
    },
    'user': {
        'model': User,
        'title' : 'gebruiker',
        'subject' :'user',
        'buttons' : ['delete', 'add', 'edit'],
        'delete_message' : u'Wilt u deze gebruiker(s) verwijderen?',
        'template': [
            {'name': 'chbx', 'data':'chbx', 'order_by': User.username, 'width': '2%', 'orderable' : False},
            {'name': 'Gebruikersnaam', 'data': 'username', 'order_by': User.username, 'orderable' : True},
            {'name': 'Voornaam', 'data': 'first_name', 'order_by': User.first_name, 'orderable' : True},
            {'name': 'Naam', 'data': 'last_name', 'order_by': User.last_name, 'orderable' : True},
            {'name': 'Email', 'data': 'email', 'order_by': User.email, 'orderable' : True},
            {'name': 'Type', 'data': 'user_type', 'order_by': User.user_type, 'orderable' : True},
            {'name': 'Login', 'data': 'last_login', 'order_by': User.last_login, 'orderable' : True},
            {'name': 'Niveau', 'data': 'level', 'order_by': User.level, 'orderable' : True},],
        'data_endpoint' : 'data',
        'filter': [],
        'href': [],
        'query_filter' : filter,
        'format_data': User.format_data,
    },
    'replacement': {
        'model': ReplacementTeacher,
        'title' : 'Vervangleerkrachten',
        'subject' :'settings.replacements',
        'buttons' : ['delete', 'add', 'edit'],
        'delete_message' : u'Wilt u deze vervanging(en) verwijderen?',
        'template': [
            {'name': 'chbx', 'data':'chbx', 'order_by': Teacher.code, 'width': '2%', 'orderable' : False},
            {'name': 'Vervanger', 'data': 'replaced_by', 'order_by': Teacher.code, 'width': '20%', 'orderable' : True},
            {'name': 'Vervangt', 'data': 'replacing', 'order_by': Teacher.code, 'orderable' : True},
        ],
        'data_endpoint' : 'data',
        'filter': [],
        'href': [],
        'format_data': ReplacementTeacher.format_data,
    }
}

