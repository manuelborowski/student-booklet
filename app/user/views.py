# -*- coding: utf-8 -*-
# app/user/views.py

from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user

from .forms import AddForm, EditForm, ViewForm, ChangePasswordForm
from .. import db, log, admin_required
from . import user
from ..models import User

from ..base_multiple_items import build_filter_and_filter_data, prepare_data_for_html
from ..base import flash_plus
from ..tables_config import  tables_configuration
from ..floating_menu import user_menu_config, admin_menu_config

#This route is called by an ajax call on the assets-page to populate the table.
@user.route('/user/data', methods=['GET', 'POST'])
@login_required
def source_data():
    return prepare_data_for_html(tables_configuration['user'])

#ashow a list of purchases
@user.route('/user', methods=['GET', 'POST'])
@admin_required
@login_required
def users():
    try:
        #The following line is required only to build the filter-fields on the page.
        _filter, _filter_form, a,b, c = build_filter_and_filter_data(tables_configuration['user'])
        config = tables_configuration['user']
        #floating menu depends if current user is admin or not
        if current_user.is_at_least_admin:
            config['floating_menu'] = admin_menu_config
        else:
            config['floating_menu'] = user_menu_config
    except Exception as e:
        log.error(u'Could not show users {}'.format(e))
        flash_plus(u'Kan gebruikers niet tonen', e)

    return render_template('base_multiple_items.html',
                           title='users',
                           filter=_filter, filter_form=_filter_form,
                           config=config)


#add a new user
@user.route('/user/add/<int:id>', methods=['GET', 'POST'])
@user.route('/user/add', methods=['GET', 'POST'])
@admin_required
@login_required
def add(id=-1):
    try:
        if id > -1:
            user = User.query.get(int(id))
            form = AddForm(obj=user)
        else:
            form = AddForm()
        del form.id # is not required here and makes validate_on_submit fail...
        #Validate on the second pass only (when button 'Bewaar' is pushed)
        if 'button' in request.form and request.form['button'] == 'Bewaar' and form.validate_on_submit():
            if form.type.data == User.USER_TYPE.LOCAL:
                password = form.password.data
            else:
                password = ''
            user = User(email=form.email.data,
                            username=form.username.data,
                            first_name=form.first_name.data,
                            last_name=form.last_name.data,
                            password=password,
                            level=form.level.data,
                            user_type = form.type.data
                        )
            db.session.add(user)
            db.session.commit()
            log.info('add : {}'.format(user.log()))
            #flash_plus('You have added user {}'.format(user.username))
            return redirect(url_for('user.users'))
    except Exception as e:
        log.error(u'Could not add user {}'.format(e))
        flash_plus(u'Kan gebruikers niet toevoegen', e)
        db.session.rollback()
        return redirect(url_for('user.users'))

    return render_template('user/user.html', form=form, title='Voeg een gebruiker toe', role='add', route='user.users', subject='user')


#edit a user
@user.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
@login_required
def edit(id):
    try:
        user = User.query.get(id)
        form = EditForm(obj=user)
        if form.validate_on_submit():
            if request.form['button'] == 'Bewaar':
                form.populate_obj(user)
                db.session.commit()
                #flash_plus('You have edited user {}'.format(user.username))
            return redirect(url_for('user.users'))
    except Exception as e:
        log.error(u'Could not edit user {}'.format(e))
        flash_plus(u'Kan gebruiker niet aanpassen', e)
        return redirect(url_for('user.users'))
    return render_template('user/user.html', form=form, title='Pas een gebruiker aan', role='edit', route='user.users', subject='user')

#no login required
@user.route('/user/view/<int:id>', methods=['GET', 'POST'])
@admin_required
def view(id):
    try:
        user = User.query.get(id)
        form = ViewForm(obj=user)
        if form.validate_on_submit():
            return redirect(url_for('user.users'))
    except Exception as e:
        log.error(u'Could not view user {}'.format(e))
        flash_plus(u'Kan gebruiker niet bekijken', e)
        return redirect(url_for('user.users'))
    return render_template('user/user.html', form=form, title='Bekijk een gebruiker', role='view', route='user.users', subject='user')

#delete a user
@user.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@user.route('/user/delete/', methods=['GET', 'POST'])
@admin_required
@login_required
def delete(id=-1):
    try:
        if id == 1:
            log.error(u'cannot delete this user')
            flash_plus(u'Kan de gebruiker admin niet verwijderen')
        elif id > -1:
            user = User.query.get(id)
            db.session.delete(user)
            db.session.commit()
        else:
            cb_id_list = request.form.getlist('cb')
            for id in cb_id_list:
                if int(id) == 1:
                    log.error(u'cannot delete this user')
                    flash_plus(u'Kan de gebruiker admin niet verwijderen')
                    continue
                user = User.query.get(int(id))
                db.session.delete(user)
            db.session.commit()
    except Exception as e:
        log.error(u'Could not delete user : {}'.format(e))
        flash_plus(u'Kan de gebruikers niet verwijderen', e)
    return redirect(url_for('user.users'))

@user.route('/user/change-password/<int:id>', methods=['GET', 'POST'])
@admin_required
@login_required
def change_pwd(id):
    try:
        user = User.query.get(id)
        form = ChangePasswordForm()
        if form.validate_on_submit():
            if user.verify_password(form.old_password.data):
                user.password = form.new_password.data
                db.session.commit()
                flash_plus(u'Je paswoord is aangepast.')
                return redirect(url_for('user.users'))
            flash_plus(u'Ongeldige gebruikersnaam of paswoord.')
    except Exception as e:
        log.erroru('Could not change password : {}'.format(e))
        flash_plus(u'Kan het paswoord niet aanpassen', e)
        return redirect(url_for('user.users'))
    return render_template('user/user.html', form=form, title='Verander paswoord', role='change_password', route='user.users', subject='user')