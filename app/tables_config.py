# -*- coding: utf-8 -*-

from models import User, Offence, Teacher, Student, Classgroup, Lesson, Type, Measure, ExtraMeasure
import user.extra_filtering
from floating_menu import default_menu_config, offence_menu_config

tables_configuration = {
    'offence' : {
        'model' : Offence,
        'title' : 'Opmerking',
        'subject' :'offences',
        'buttons' : ['delete', 'edit', 'start_check'],
        'delete_message' : 'Wilt u deze opmerking(en) verwijderen?',
        'template' : [{'name': 'cb', 'data':'cb', 'order_by': Offence.timestamp, 'width': '1%', 'orderable' : False},
                      {'name': 'Datum', 'data':'date', 'order_by': Offence.timestamp, 'width': '12%', 'orderable' : True},
                      {'name': 'Leerling', 'data':'student.full_name', 'order_by': Student.last_name, 'width': '10%', 'orderable' : True},
                      {'name': '#', 'data':'student.number', 'order_by': lambda k: k['student']['number'], 'width': '1%', 'orderable' : True},
                      {'name': 'LKR', 'data':'teacher.code', 'order_by': Teacher.code, 'width': '1%', 'orderable' : True},
                      {'name': 'KL', 'data':'classgroup.name', 'order_by': Classgroup.name, 'width': '1%', 'orderable' : True},
                      {'name': 'Les', 'data':'lesson.name', 'order_by': Lesson.name, 'width': '5%', 'orderable' : True},
                      {'name': 'Opmerking', 'data':'types', 'order_by': lambda k: k['types'], 'width': '30%', 'orderable' : True},
                      {'name': 'Maatregel', 'data':'measures', 'order_by': lambda k: k['measures'], 'width': '30%', 'orderable' : True},
                      ],
        'filter' :  ['date', 'teacher', 'classgroup', 'lesson', 'reviewed'],
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
        'title' : 'Extra opmerking',
        'subject' :'review',
        'buttons' : ['start_check'],
        'delete_message' : 'Wilt u deze opmerking(en) verwijderen?',
        'template' : [
                      {'name': 'Datum', 'data':'date', 'order_by': ExtraMeasure.timestamp, 'width': '12%', 'orderable' : True},
                      {'name': 'Leerling', 'data':'offence.student.full_name', 'order_by': Student.last_name, 'width': '10%', 'orderable' : True},
                      {'name': 'LKR', 'data':'offence.teacher.code', 'order_by': Teacher.code, 'width': '1%', 'orderable' : True},
                      {'name': 'KL', 'data':'offence.classgroup.name', 'order_by': Classgroup.name, 'width': '1%', 'orderable' : True},
                      {'name': 'Les', 'data':'offence.lesson.name', 'order_by': Lesson.name, 'width': '5%', 'orderable' : True},
                      {'name': 'Maatregel', 'data':'note', 'order_by': lambda k: k['measures'], 'width': '30%', 'orderable' : True},
                      ],
        'filter' :  ['date', 'teacher', 'classgroup', 'lesson', 'reviewed'],
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
    'user': {
        'model': User,
        'title' : 'gebruiker',
        'subject' :'user',
        'buttons' : ['delete'],
        'delete_message' : 'Wilt u deze gebruiker(s) verwijderen?',
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

