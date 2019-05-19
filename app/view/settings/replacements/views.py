from flask import render_template, redirect, url_for, request
from flask_login import login_required

from . import replacements, forms
from app import db, log, supervisor_required


from app.utils import utils
from app.database.models import ReplacementTeacher
from app.database import db_utils, db_teacher, db_replacement, multiple_items
from app.layout import tables_config


@replacements.route('/settings/replacements/show', methods=['GET', 'POST'])
@supervisor_required
@login_required
def show():
    _filter, _filter_form, a,b, c = multiple_items.process_data(tables_config.tables_configuration['replacement'])
    return render_template('base_multiple_items.html',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_config.tables_configuration['replacement'])


@replacements.route('/settings/replacements/data', methods=['GET', 'POST'])
@supervisor_required
@login_required
def data():
    ajax_table =  multiple_items.prepare_data_for_html(tables_config.tables_configuration['replacement'])
    return ajax_table



@replacements.route('/settings/replacements/action', methods=['GET', 'POST'])
@login_required
@supervisor_required
def action():
    if utils.button_pressed('add'):
        return add()
    if utils.button_pressed('edit'):
        return edit()
    if utils.button_pressed('delete'):
        return delete()
    return redirect(url_for('settings.replacements.show'))


@replacements.route('/settings/replacements/action_done/<string:action>/<int:id>', methods=['GET', 'POST'])
@replacements.route('/settings/replacements/action_done/<string:action>', methods=['GET', 'POST'])
@login_required
@supervisor_required
def action_done(action=None, id=-1):
    if utils.button_pressed('save'):
        if action == 'add':
            return add(action_done=True)
        if action == 'edit':
            return edit(action_done=True)
    return redirect(url_for('settings.replacements.show'))


def add(action_done=False):
    try:
        if action_done:
            absent_teacher_ids = request.form.getlist('my-select[]')
            replaced_by_teacher_id = request.form['replaced_by']
            school = db_utils.school()
            academic_year = db_utils.academic_year()
            if absent_teacher_ids:
                for t_id in absent_teacher_ids:
                    r = ReplacementTeacher(replacing_id=t_id, replaced_by_id=replaced_by_teacher_id, school=school, academic_year=academic_year)
                    db.session.add(r)
                r.first_replacement_teacher = True
                db.session.commit()
        else:
            form = forms.AddForm()
            teachers = [(i, t, '') for i, t in db_teacher.db_teacher_list(select=True, full_name=True)]
            return render_template('settings/replacements/replacement.html', form=form, all_teachers=teachers, title='Voeg een vervanger toe',
                                   action='add', role='add', subject='settings.replacements')
    except Exception as e:
        log.error(u'Could not add replacement {}'.format(e))
        utils.flash_plus(u'Kan vervanger niet toevoegen', e)
        db.session.rollback()
    return redirect(url_for('settings.replacements.show'))

def edit(action_done=False, id=-1):
    try:
        if action_done:
            absent_teacher_ids = request.form.getlist('my-select[]')
            replaced_by_teacher_id = request.form['replaced_by']
            school = db_utils.school()
            academic_year = db_utils.academic_year()
            for r in db_replacement.replacement_list(id=replaced_by_teacher_id):
                db.session.delete(r)
            if absent_teacher_ids:
                for t_id in absent_teacher_ids:
                    r = ReplacementTeacher(replacing_id=t_id, replaced_by_id=replaced_by_teacher_id, school=school, academic_year=academic_year)
                    db.session.add(r)
                r.first_replacement_teacher = True
            db.session.commit()
        else:
            chbx_id_list = request.form.getlist('chbx')
            if chbx_id_list:
                id = int(chbx_id_list[0])  # only the first one can be edited
                absent_teacher_ids = db_replacement.replacement_list(id=id, ids_only=True)
                # absent_teachers = db_teacher.db_teacher_list(select=True, full=True, id_list=replacements)
                all_teachers = db_teacher.db_teacher_list(select=True, full_name=True)
                filtered_teachers = []
                for i, t in all_teachers:
                    if i in absent_teacher_ids:
                        filtered_teachers.append((i, t, 'selected'))
                    else:
                        filtered_teachers.append((i, t, ''))

                form = forms.EditForm()
                form.replaced_by.choices = [(id, db_teacher.db_teacher(id=id, full_name=True))]
                return render_template('settings/replacements/replacement.html', form=form, all_teachers=filtered_teachers,
                                       title='Wijzig een vervanger toe',
                                       action='edit', role='edit', subject='settings.replacements')

    except Exception as e:
        log.error(u'Could not edit replacement {}'.format(e))
        utils.flash_plus(u'Kan vervanger niet wijzigen', e)
        db.session.rollback()
    return redirect(url_for('settings.replacements.show'))

def delete():
    try:
        chbx_id_list = request.form.getlist('chbx')
        for id in chbx_id_list:
            for r in db_replacement.replacement_list(id=id):
                db.session.delete(r)
        db.session.commit()

    except Exception as e:
        log.error(u'Could not delete replacement {}'.format(e))
        utils.flash_plus(u'Kan vervanger niet verwijderen', e)
        db.session.rollback()
    return redirect(url_for('settings.replacements.show'))
