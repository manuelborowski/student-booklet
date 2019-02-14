# -*- coding: utf-8 -*-
# app/user/views.py

from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user

from .forms import AddForm, EditForm, ViewForm, ChangePasswordForm
from .. import db, log, admin_required
from . import user
from ..models import User

from ..base_multiple_items import build_filter_and_filter_data, prepare_data_for_html
from ..base import flash_plus, button_save_pushed
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
def show():
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
        if button_save_pushed(): #second pass
            form = AddForm()
            if form.validate_on_submit():
                if form.user_type.data == User.USER_TYPE.LOCAL:
                    password = form.password.data
                else:
                    password = ''
                user = User(email=form.email.data,
                                username=form.username.data,
                                first_name=form.first_name.data,
                                last_name=form.last_name.data,
                                password=password,
                                level=form.level.data,
                                user_type = form.user_type.data
                            )
                db.session.add(user)
                db.session.commit()
                log.info('add : {}'.format(user.log()))
                return redirect(url_for('user.show'))
            else:
                return render_template('user/user.html', form=form, title='Voeg een gebruiker toe', role='add',
                                       subject='user')
        else: #first pass
            if id > -1: #copy from existing user
                user = User.query.get(id)
                form = AddForm(obj=user)
            else:
                form = AddForm()
            return render_template('user/user.html', form=form, title='Voeg een gebruiker toe', role='add', subject='user')
    except Exception as e:
        log.error(u'Could not add user {}'.format(e))
        flash_plus(u'Kan gebruikers niet toevoegen', e)
        db.session.rollback()
    return redirect(url_for('user.show'))


@user.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@user.route('/user/edit', methods=['GET', 'POST'])
@admin_required
@login_required
def edit(id=-1):
    try:
        if button_save_pushed(): #second pass
            user = User.query.get(id)
            form = EditForm(id=id)
            if form.validate_on_submit():
                form.populate_obj(user)
                db.session.commit()
                return redirect(url_for('user.show'))
            else:
                return render_template('user/user.html', form=form, title='Wijzig een gebruiker', role='edit', subject='user')
        else: #first pass
            if id == -1:
                cb_id_list = request.form.getlist('cb')
                if cb_id_list:
                    id = int(cb_id_list[0]) #only the first one can be edited
                    user = User.query.get(id)
                    form = EditForm(obj=user, formdata=None)
                else:
                    return redirect(url_for('user.show'))
            else:
                user = User.query.get(id)
                form = EditForm(obj=user)
            return render_template('user/user.html', form=form, title='Wijzig een gebruiker', role='edit', subject='user')
    except Exception as e:
        log.error(u'Could not edit user {}'.format(e))
        flash_plus(u'Kan gebruiker niet aanpassen', e)
    return redirect(url_for('user.show'))

#no login required
@user.route('/user/view/<int:id>', methods=['GET', 'POST'])
@admin_required
def view(id):
    try:
        user = User.query.get(id)
        form = ViewForm(obj=user)
    except Exception as e:
        log.error(u'Could not view user {}'.format(e))
        flash_plus(u'Kan gebruiker niet bekijken', e)
        return redirect(url_for('user.show'))
    return render_template('user/user.html', form=form, title='Bekijk een gebruiker', role='view', subject='user')

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
    return redirect(url_for('user.show'))

@user.route('/user/change_password/<int:id>', methods=['GET', 'POST'])
@admin_required
@login_required
def change_password(id):
    try:
        if button_save_pushed(): #second pass
            user = User.query.get(id)
            form = ChangePasswordForm(id=id)
            if form.validate_on_submit():
                user.password = form.new_password.data
                db.session.commit()
                flash_plus(u'Het paswoord is aangepast.')
                return redirect(url_for('user.show'))
            else:
                return render_template('user/user.html', form=form, title='Verander paswoord', role='change_password', subject='user')
        else: #first pass
            user = User.query.get(id)
            if user.is_oauth:
                flash_plus(u'Deze gebruiker heeft geen paswoord', u'Dit is een OAUTH-gebruiker')
                return redirect(url_for('user.show'))
            form = ChangePasswordForm(obj=user)
        return render_template('user/user.html', form=form, title='Verander paswoord', role='change_password', subject='user')
    except Exception as e:
        log.error('Could not change password : {}'.format(e))
        flash_plus(u'Kan het paswoord niet aanpassen', e)
    return redirect(url_for('user.show'))
