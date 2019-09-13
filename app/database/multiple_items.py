# -*- coding: utf-8 -*-
from wtforms.widgets.core import html_params
from wtforms.widgets import HTMLString
from wtforms import BooleanField
from flask import request, get_flashed_messages, jsonify
from sqlalchemy import or_
import time

import app.database.db_utils
from app.database.models import User, Teacher, Grade, Lesson, Student, Remark, ExtraMeasure, ReplacementTeacher
from app.layout.forms import GradeFilter, TeacherFilter, SchoolyearFilter
from app import log, db
from app.utils import utils

class InlineButtonWidget(object):
    """
    Render a basic ``<button>`` field.
    """
    input_type = 'submit'
    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        kwargs.setdefault('value', field.label.text)
        return HTMLString('<input %s>' % self.html_params(name=field.name, **kwargs))


class InlineSubmitField(BooleanField):
    """
    Represents an ``<button type="submit">``.  This allows checking if a given
    submit button has been pressed.
    """
    widget = InlineButtonWidget()

######################################################################################################
###                                       Build a generic filter
######################################################################################################

def check_date_in_form(date_key, form):
    if date_key in form and form[date_key] != '':
        try:
            time.strptime(form[date_key].strip(), '%d-%M-%Y')
            return form[date_key].strip()
        except Exception as e:
            utils.flash_plus('Verkeerd datumformaat, moet in de vorm zijn : d-m-y', e)
    return ''

def check_value_in_form(value_key, form):
    if value_key in form and form[value_key] != '':
        try:
            float(form[value_key])
            return form[value_key]
        except Exception as e:
            utils.flash_plus('Verkeerde getal notatie', e)
    return ''

def check_string_in_form(value_key, form):
    if value_key in form and form[value_key] != '':
        try:
            str(form[value_key])
            return form[value_key]
        except Exception as e:
            utils.flash_plus('Verkeerde tekst notatie', e)
    return ''

def create_filter_form():
    filter_form = {}
    filter_form['academic_year'] = SchoolyearFilter()
    filter_form['teacher'] = TeacherFilter()
    filter_form['grade'] = GradeFilter()
    return filter_form


def process_data(table, paginate=True):
    _model = table['model']
    _filters_enabled = table['filter']
    _template = table['template']

    if _model is Remark:
        _filtered_list = db.session.query(Remark, Student, Grade, Teacher, Lesson).join(Student, Student.id == Remark.student_id) \
            .join(Grade, Grade.id == Remark.grade_id).join(Teacher, Teacher.id == Remark.teacher_id).join(Lesson, Lesson.id == Remark.lesson_id)\
            .filter(Remark.school == app.database.db_utils.school())
    elif _model is ExtraMeasure:
        _filtered_list = db.session.query(ExtraMeasure, Remark, Student, Grade).join(Remark, Remark.extra_measure_id == ExtraMeasure.id)\
            .join(Student, Student.id == Remark.student_id).join(Grade, Grade.id == Remark.grade_id)\
            .filter(Remark.reviewed == True, Remark.first_remark == True, Remark.school == app.database.db_utils.school())
    elif _model is ReplacementTeacher:
        _filtered_list = db.session.query(ReplacementTeacher, Teacher).join(Teacher, ReplacementTeacher.replaced_by_id == Teacher.id)
    else:
        _filtered_list = db.session.query(User)

    if 'query_filter' in table:
        _filtered_list = table['query_filter'](_filtered_list)

    _total_count = _filtered_list.count()

    _filter_forms = {}

    #Create the sql-request with the apropriate filters
    if 'academic_year' in _filters_enabled:
        _filter_forms['academic_year'] = SchoolyearFilter()
        value = check_string_in_form('academic_year', request.values)
        if value != '':
            _filtered_list = _filtered_list.filter(Remark.academic_year == value)

    if 'teacher' in _filters_enabled:
        _filter_forms['teacher'] = TeacherFilter()
        value = check_value_in_form('teacher', request.values)
        if value and int(value) > -1:
            _filtered_list = _filtered_list.filter(Teacher.id == value)

    if 'grade' in _filters_enabled:
        _filter_forms['grade'] = GradeFilter()
        value = check_value_in_form('grade', request.values)
        if value and int(value) > -1:
            _filtered_list = _filtered_list.filter(Grade.id == value)

    if 'reviewed' in _filters_enabled:
        value = check_string_in_form('reviewed', request.values)
        if value == 'true':
            _filtered_list = _filtered_list.filter(Remark.reviewed == True, Remark.extra_measure_id != None).join(ExtraMeasure)
        elif value == 'false' or value == '': #default
            _filtered_list = _filtered_list.filter(Remark.reviewed == False)

    #search, if required
    #from template, take order_by and put in a list.  This is user later on, to get the columns in which can be searched
    column_list = [a['order_by'] for a in _template]
    search_value = check_string_in_form('search[value]', request.values)
    if search_value:
        a = search_value.split('-')[::-1]
        a[0] += '%'
        search_date = '%' + '-'.join(a) + '%'
        search_value = '%' + search_value + '%'
        search_constraints = []
        #if Offence.timestamp in column_list:
        #    search_constraints.append(Offence.timestamp.like(search_value))
        if Student.full_name in column_list:
            search_constraints.append(Student.full_name.like(search_value))
        if Student.first_name in column_list:
            search_constraints.append(Student.first_name.like(search_value))
        if Teacher.code in column_list:
            search_constraints.append(Teacher.code.like (search_date))
        if Grade.code in column_list:
            search_constraints.append(Grade.code.like(search_value))
        if Lesson.code in column_list:
            search_constraints.append(Lesson.code.like(search_value))
        if User.username in column_list:
            search_constraints.append(User.username.like(search_value))
        if User.first_name in column_list:
            search_constraints.append(User.first_name.like(search_value))
        if User.last_name in column_list:
            search_constraints.append(User.last_name.like(search_value))
        if User.email in column_list:
            search_constraints.append(User.email.like(search_value))

        if search_constraints:
            _filtered_list = _filtered_list.filter(or_(*search_constraints))

    _filtered_count = _filtered_list.count()
    
    #order, if required, first stage
    column_number = check_value_in_form('order[0][column]', request.values)
    if column_number:
        column_number = int(column_number)
        if 'row_detail' in table:
            column_number -= 1
        column_name = check_string_in_form('columns[' + str(column_number) + '][data]', request.values)
        if _template[column_number]['order_by'] and  not callable(_template[column_number]['order_by']) :
            direction = check_string_in_form('order[0][dir]', request.values)
            if direction == 'desc':
                _filtered_list = _filtered_list.order_by(_template[column_number]['order_by'].desc())
            else:
                _filtered_list = _filtered_list.order_by(_template[column_number]['order_by'])

    if paginate:
        #paginate, if required
        start = check_value_in_form('start', request.values)
        if start:
            length = int(check_value_in_form('length', request.values))
            start = int(start)
            _filtered_list = _filtered_list.slice(start, start+length)

    _filtered_list = _filtered_list.all()

    return _filters_enabled,  _filter_forms, _filtered_list, _total_count, _filtered_count,



def prepare_data_for_html(table):
    try:
        _filters_enabled,  _filter_forms, _filtered_list, _total_count, _filtered_count = process_data(table)
        _filtered_dict = table['format_data'](_filtered_list)

        #order, if required, 2nd stage
        _template = table['template']
        column_number = check_value_in_form('order[0][column]', request.values)
        column_number = int(column_number)
        if column_number:
            if 'row_detail' in table:
                column_number -= 1
            if _template[column_number]['order_by'] and  callable(_template[column_number]['order_by']):
                reverse = False if check_string_in_form('order[0][dir]', request.values) == 'desc' else True
                _filtered_dict = sorted(_filtered_dict, key= _template[column_number]['order_by'], reverse=reverse)
    except Exception as e:
        log.error('could not prepare data for html : {}'.format(e))
        utils.flash_plus('Er is een fout opgetreden en de tabel kan niet getoond worden.', e)
        _total_count = _filtered_list = _filtered_count = 0
        _filtered_dict = []

    #prepare for json/ajax
    output = {}
    output['draw'] = str(int(request.values['draw']))
    output['recordsTotal'] = str(_total_count)
    output['recordsFiltered'] = str(_filtered_count)
    output['data'] = _filtered_dict
    # add the (non-standard) flash-tag to display flash-messages via ajax
    fml = get_flashed_messages()
    if not not fml:
        output['flash'] = fml
    return  jsonify(output)
