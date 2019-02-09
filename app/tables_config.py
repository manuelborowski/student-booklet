# -*- coding: utf-8 -*-

from models import User, Remark, Teacher, Student, Grade, Lesson, RemarkSubject, RemarkMeasure, ExtraMeasure
import user.extra_filtering
from floating_menu import default_menu_config, offence_menu_config

tables_configuration = {
    'remark' : {
        'model' : Remark,
        'title' : 'Boekje',
        'subject' :'remarks',
        'buttons' : ['delete', 'edit', 'start_check'],
        'delete_message' : u'Wilt u deze opmerking(en) verwijderen?',
        'template' : [{'name': 'cb', 'data':'cb', 'order_by': Remark.timestamp, 'width': '1%', 'orderable' : False},
                      {'name': 'Datum', 'data':'date', 'order_by': Remark.timestamp, 'width': '12%', 'orderable' : True},
                      {'name': 'Leerling', 'data':'student.full_name', 'order_by': Student.last_name, 'width': '10%', 'orderable' : True},
                      {'name': '#', 'data':'student.number', 'order_by': lambda k: k['student']['number'], 'width': '1%', 'orderable' : True},
                      {'name': 'LKR', 'data':'teacher.code', 'order_by': Teacher.code, 'width': '1%', 'orderable' : True},
                      {'name': 'KL', 'data':'grade.code', 'order_by': Grade.code, 'width': '1%', 'orderable' : True},
                      {'name': 'Les', 'data':'lesson.code', 'order_by': Lesson.code, 'width': '5%', 'orderable' : True},
                      {'name': 'Opmerking', 'data':'subjects', 'order_by': lambda k: k['subjects'], 'width': '30%', 'orderable' : True},
                      {'name': 'Maatregel', 'data':'measures', 'order_by': lambda k: k['measures'], 'width': '30%', 'orderable' : True},
                      ],
        'filter' :  ['schoolyear', 'teacher', 'grade', 'lesson', 'reviewed'],
        'href': [],
        # 'href': [{'attribute': '["name"]', 'route': '"asset.view"', 'id': '["id"]'},
        #          {'attribute': '["purchase"]["since"]', 'route': '"purchase.view"', 'id': '["purchase"]["id"]'},
        #          {'attribute': '["purchase"]["supplier"]["name"]', 'route': '"supplier.view"', 'id': '["purchase"]["supplier"]["id"]'},
        #          {'attribute': '["purchase"]["device"]["brandtype"]', 'route': '"device.view"', 'id': '["purchase"]["device"]["id"]'}
        #          ],
        'floating_menu' : [],
        'disable_add_button' : True,
        #'export' : 'asset.exportcsv',
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
                      {'name': 'Maatregel', 'data':'note', 'order_by': lambda k: k['measures'], 'width': '30%', 'orderable' : True},
                      ],
        'filter' :  ['schoolyear', 'teacher', 'grade', 'lesson'],
        'href': [],
        'floating_menu' : [],
        'disable_add_button' : True,
        #'export' : 'asset.exportcsv',
        'row_detail' : 'reviewed',
    },
    'user': {
        'model': User,
        'title' : 'gebruiker',
        'subject' :'user',
        'buttons' : ['delete', 'add', 'edit'],
        'delete_message' : u'Wilt u deze gebruiker(s) verwijderen?',
        'template': [
            {'name': 'cb', 'data':'cb', 'order_by': User.username, 'width': '2%', 'orderable' : False},
            {'name': 'Gebruikersnaam', 'data': 'username', 'order_by': User.username, 'orderable' : True},
            {'name': 'Voornaam', 'data': 'first_name', 'order_by': User.first_name, 'orderable' : True},
            {'name': 'Naam', 'data': 'last_name', 'order_by': User.last_name, 'orderable' : True},
            {'name': 'Email', 'data': 'email', 'order_by': User.email, 'orderable' : True},
            {'name': 'Type', 'data': 'user_type', 'order_by': User.user_type, 'orderable' : True},
            {'name': 'Login', 'data': 'last_login', 'order_by': User.last_login, 'orderable' : True},
            {'name': 'Niveau', 'data': 'level', 'order_by': User.level, 'orderable' : True},],
        'filter': [],
        'href': [{'attribute': '["username"]', 'route': '"user.view"', 'id': '["id"]'},
                 ],
        'floating_menu' : default_menu_config,
        'query_filter' : user.extra_filtering.filter,
    }
}

