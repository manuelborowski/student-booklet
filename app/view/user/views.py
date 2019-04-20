# -*- coding: utf-8 -*-
# app/user/views.py

from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user

from .forms import AddForm, EditForm
from app import db, log, admin_required
from . import user
from app.database.models import User

from app.database.multiple_items import build_filter_and_filter_data, prepare_data_for_html
from app.utils import utils
from app.layout.tables_config import tables_configuration


# This route is called by an ajax call on the assets-page to populate the table.
@user.route('/user/data', methods=['GET', 'POST'])
@login_required
def data():
    return prepare_data_for_html(tables_configuration['user'])


# ashow a list of purchases
@user.route('/user', methods=['GET', 'POST'])
@admin_required
@login_required
def show():
    try:
        # The following line is required only to build the filter-fields on the page.
        _filter, _filter_form, a, b, c = build_filter_and_filter_data(tables_configuration['user'])
    except Exception as e:
        log.error(u'Could not show users {}'.format(e))
        utils.flash_plus(u'Kan gebruikers niet tonen', e)

    return render_template('base_multiple_items.html', title='users', filter=_filter, filter_form=_filter_form,
                           config=tables_configuration['user'])


@user.route('/user/action', methods=['GET', 'POST'])
@login_required
@admin_required
def action():
    if utils.button_pressed('add'):
        return add()
    if utils.button_pressed('edit'):
        return edit()
    if utils.button_pressed('delete'):
        return delete()
    if utils.button_pressed('change-password'):
        return change_password()
    return redirect(url_for('user.show'))


@user.route('/user/action_done/<string:action>/<int:id>', methods=['GET', 'POST'])
@user.route('/user/action_done/<string:action>', methods=['GET', 'POST'])
@login_required
@admin_required
def action_done(action=None, id=-1):
    if utils.button_pressed('save'):
        if action == 'add':
            return add(action_done=True)
        if action == 'edit':
            return edit(action_done=True, id=id)
        if action == 'change-password':
            return change_password(action_done=True, id=id)

    return redirect(url_for('user.show'))


def add(action_done=False):
    try:
        if action_done:
            form = AddForm()
            if form.validate_on_submit():
                if form.user_type.data == User.USER_TYPE.LOCAL:
                    password = form.password.data
                else:
                    password = ''
                user = User(email=form.email.data,username=form.username.data,first_name=form.first_name.data,last_name=form.last_name.data,
                            password=password,level=form.level.data,user_type=form.user_type.data)
                db.session.add(user)
                db.session.commit()
                log.info('add : {}'.format(user.log()))
                return redirect(url_for('user.show'))
            else:
                return render_template('user/user.html', form=form, title='Voeg een gebruiker toe', action='add', role='add', subject='user')
        else:
            form = AddForm()
            return render_template('user/user.html', form=form, title='Voeg een gebruiker toe', action='add', role='add', subject='user')
    except Exception as e:
        log.error(u'Could not add user {}'.format(e))
        utils.flash_plus(u'Kan gebruikers niet toevoegen', e)
        db.session.rollback()
    return redirect(url_for('user.show'))


def edit(action_done=False, id=-1):
    try:
        if action_done:
            user = User.query.get(id)
            form = EditForm(id=id)
            if form.validate_on_submit():
                form.populate_obj(user)
                db.session.commit()
                return redirect(url_for('user.show'))
            else:
                return render_template('user/user.html', form=form, title='Wijzig een gebruiker', action='edit', role='edit', subject='user')
        else:
            chbx_id_list = request.form.getlist('chbx')
            if chbx_id_list:
                id = int(chbx_id_list[0])  # only the first one can be edited
                user = User.query.get(id)
                form = EditForm(obj=user, formdata=None)
            else:
                return redirect(url_for('user.show'))
            return render_template('user/user.html', form=form, title='Wijzig een gebruiker', action='edit', role='edit', subject='user')
    except Exception as e:
        log.error(u'Could not edit user {}'.format(e))
        utils.flash_plus(u'Kan gebruiker niet aanpassen', e)
    return redirect(url_for('user.show'))


# no login required
@user.route('/user/view/<int:id>', methods=['GET', 'POST'])
@admin_required
def view(id):
    try:
        user = User.query.get(id)
        form = ViewForm(obj=user)
    except Exception as e:
        log.error(u'Could not view user {}'.format(e))
        utils.flash_plus(u'Kan gebruiker niet bekijken', e)
        return redirect(url_for('user.show'))
    return render_template('user/user.html', form=form, title='Bekijk een gebruiker', role='view', subject='user')


def delete():
    try:
        chbx_id_list = request.form.getlist('chbx')
        for id in chbx_id_list:
            if int(id) == 1:
                log.error(u'cannot delete this user')
                utils.flash_plus(u'Kan de gebruiker admin niet verwijderen')
                continue
            if int(id) == current_user.id:
                log.error(u'user cannot delete himself')
                utils.flash_plus(u'Een gebruiker kan niet zichzelf verwijderen.')
                continue
            user = User.query.get(int(id))
            db.session.delete(user)
        db.session.commit()
    except Exception as e:
        log.error(u'Could not delete user : {}'.format(e))
        utils.flash_plus(u'Kan de gebruikers niet verwijderen', e)
    return redirect(url_for('user.show'))

def change_password(action_done=False, id=-1):
    try:
        if action_done:
            user = User.query.get(id)
            form = ChangePasswordForm(id=id)
            if form.validate_on_submit():
                user.password = form.new_password.data
                db.session.commit()
                utils.flash_plus(u'Het paswoord is aangepast.')
                return redirect(url_for('user.show'))
            else:
                return render_template('user/user.html', form=form, title='Verander paswoord', action='change-password', role='change-password', subject='user')
        else:
            chbx_id_list = request.form.getlist('chbx')
            if chbx_id_list:
                id = int(chbx_id_list[0])  # only the first one can be edited
                user = User.query.get(id)
                if user.is_oauth:
                    utils.flash_plus(u'Deze gebruiker heeft geen paswoord', u'Dit is een OAUTH-gebruiker')
                    return redirect(url_for('user.show'))
                form = ChangePasswordForm(obj=user)
        return render_template('user/user.html', form=form, title='Verander paswoord', action='change-password', role='change-password', subject='user')
    except Exception as e:
        log.error('Could not change password : {}'.format(e))
        utils.flash_plus(u'Kan het paswoord niet aanpassen', e)
    return redirect(url_for('user.show'))
