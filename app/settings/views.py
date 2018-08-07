# -*- coding: utf-8 -*-
# app/settings/views.py

from flask import render_template, redirect, url_for, request, flash, send_file, abort
from flask_login import login_required, current_user
from ..base import get_setting_inc_index_asset_name, set_setting_inc_index_asset_name, get_setting_copy_from_last_add, set_setting_copy_from_last_add
from . import settings
from .. import db, app, log
from ..models import Settings, Classgroup, Student
from flask_login import current_user

import os
import unicodecsv  as  csv
import zipfile

def check_admin():
    if not current_user.is_admin:
        abort(403)

def get_settings_and_show():
    #inc_index_asset_name : if true and this asset is used as base to copy from, then the index of the asset name
    #will be incremented by one
    inc_index_asset_name = get_setting_inc_index_asset_name()
    #copy_from_last_add : if a url-shortcut with qr code is uses, and the qr code is not found, then a new asset is
    #added which is a copy from the previous added asset.
    copy_from_last_add = get_setting_copy_from_last_add()
    return render_template('settings/settings.html',
                           inc_index_asset_name=inc_index_asset_name,
                           copy_from_last_add=copy_from_last_add,
                           title='settings')

@settings.route('/settings', methods=['GET', 'POST'])
@login_required
def show():
    return get_settings_and_show()

@settings.route('/settings/save', methods=['GET', 'POST'])
@login_required
def save():
    if request.form['button'] == 'Bewaar':
        set_setting_inc_index_asset_name(True if 'inc_index_asset_name' in request.form else False)
        set_setting_copy_from_last_add(True if 'copy_from_last_add' in request.form else False)

    return get_settings_and_show()

#NAAM           last_name
#VOORNAAM       first_name
#LEERLINGNUMMER number
#FOTO           photo
#KLAS           classgroup_id

@settings.route('/settings/import_students', methods=['GET', 'POST'])
@login_required
def import_students():
    try:
        if request.files['import_filename']:
            # format csv file :
            log.info('Import from : {}'.format(request.files['import_filename']))
            students_file = csv.DictReader(request.files['import_filename'],  delimiter=';', encoding='utf-8-sig')

            nbr_students = 0
            nbr_classgroups = 0

            for s in students_file:
                #skip empy records
                if s['VOORNAAM'] != '' and s['NAAM'] != '' and s['LEERLINGNUMMER'] != '' and s['FOTO'] != '':
                    #check for classgroup.  If it not exists, add it first
                    classgroup = Classgroup.query.filter(Classgroup.name==s['KLAS']).first()
                    if not classgroup:
                        classgroup = Classgroup(name=s['KLAS'])
                        db.session.add(classgroup)
                        nbr_classgroups += 1
                    #add student
                    student = Student(first_name=s['VOORNAAM'], last_name=s['NAAM'], number=int(s['LEERLINGNUMMER']), photo=s['FOTO'], classgroup=classgroup)
                    nbr_students += 1

            db.session.commit()
            log.info('import: added {} students and {} classgroups'.format(nbr_students, nbr_classgroups))

    except Exception as e:
        flash('Kan bestand niet importeren')
    return redirect(url_for('settings.show'))