# -*- coding: utf-8 -*-
from wtforms.widgets.core import html_params
from wtforms.widgets import HTMLString
from wtforms import BooleanField
from flask import request, get_flashed_messages, jsonify, url_for
from sqlalchemy import or_
import time, cgi
from .models import User, Teacher, Grade, Lesson, Student, Remark, ExtraMeasure
from .forms import GradeFilter, TeacherFilter, SchoolyearFilter
from . import log
from .base import flash_plus

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
            flash_plus('Verkeerd datumformaat, moet in de vorm zijn : d-m-y', e)
    return ''

def check_value_in_form(value_key, form):
    if value_key in form and form[value_key] != '':
        try:
            float(form[value_key])
            return form[value_key]
        except Exception as e:
            flash_plus('Verkeerde getal notatie', e)
    return ''

def check_string_in_form(value_key, form):
    if value_key in form and form[value_key] != '':
        try:
            str(form[value_key])
            return form[value_key]
        except Exception as e:
            flash_plus('Verkeerde tekst notatie', e)
    return ''

def build_filter_and_filter_data(table, paginate=True):
    #depending on the table, multiple joins are required to get the necessary data
    _model = table['model']
    _filters_enabled = table['filter']
    _template = table['template']
    _filtered_list = _model.query

    if _model is Remark:
        _filtered_list = _filtered_list.join(Student)
        _filtered_list = _filtered_list.join(Grade)
        _filtered_list = _filtered_list.join(Teacher)
        _filtered_list = _filtered_list.join(Lesson)

    if _model is ExtraMeasure:
        _filtered_list = _filtered_list.join(Remark)
        _filtered_list = _filtered_list.join(Student)
        _filtered_list = _filtered_list.join(Grade)
        _filtered_list = _filtered_list.join(Teacher)
        _filtered_list = _filtered_list.join(Lesson).filter(Remark.reviewed == True)



    # if ('category' in _filters_enabled or 'device' in _filters_enabled) and _model is not Device:
    #     _filtered_list = _filtered_list.join(Device)
    # if 'supplier' in _filters_enabled and _model is not Supplier :
    #     _filtered_list = _filtered_list.join(Supplier)

    if 'query_filter' in table:
        _filtered_list = table['query_filter'](_filtered_list)

    _total_count = _filtered_list.count()

    _filter_forms = {}

    #Create the sql-request with the apropriate filters
    if 'date' in _filters_enabled:
        date = check_date_in_form('date_after', request.values)
        if date:
            _filtered_list = _filtered_list.filter(Remark.timestamp >= Remark.reverse_date(date))
        date = check_date_in_form('date_before', request.values)
        if date:
            _filtered_list = _filtered_list.filter(Remark.timestamp <= Remark.reverse_date(date))

    if 'schoolyear' in _filters_enabled:
        _filter_forms['schoolyear'] = SchoolyearFilter()
        value = check_string_in_form('schoolyear', request.values)
        if value != '':
            _filtered_list = _filtered_list.filter(Student.schoolyear == value)

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


    # if 'lesson' in _filters_enabled:
    #     _filter_forms['category'] = CategoryFilter()
    #     value = check_string_in_form('category', request.values)
    #     if value:
    #         _filtered_list = _filtered_list.filter(Device.category == value)

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
        if Student.last_name in column_list:
            search_constraints.append(Student.last_name.like(search_value))
        if Student.last_name in column_list:
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
        column_name = check_string_in_form('columns[' + str(column_number) + '][data]', request.values)
        if _template[int(column_number)]['order_by'] and  not callable(_template[int(column_number)]['order_by']) :
            direction = check_string_in_form('order[0][dir]', request.values)
            if direction == 'desc':
                _filtered_list = _filtered_list.order_by(_template[int(column_number)]['order_by'].desc())
            else:
                _filtered_list = _filtered_list.order_by(_template[int(column_number)]['order_by'])

    if paginate:
        #paginate, if required
        start = check_value_in_form('start', request.values)
        if start:
            length = int(check_value_in_form('length', request.values))
            start = int(start)
            _filtered_list = _filtered_list.slice(start, start+length)


    _filtered_list = _filtered_list.all()

    return _filters_enabled,  _filter_forms, _filtered_list, _total_count, _filtered_count,



def prepare_data_for_html(table, only_checkbox_for=None):
    try:
        _filters_enabled,  _filter_forms, _filtered_list, _total_count, _filtered_count = build_filter_and_filter_data(table)
        _filtered_dict = [i.ret_dict() for i in _filtered_list] #objects to dictionary
        for i in _filtered_dict: #some columns are links to other pages
            for h in table['href']:
                exec("i" + h['attribute'] + "= \"<a href=\\\"{}\\\">{}</a>\".format(url_for(" + h['route'] + ", id=i" + h['id'] + "), i" + h['attribute'] + ')')
            i['DT_RowId'] = i['id']
        if _filtered_dict and 'cb' in _filtered_dict[0]: #rows in the table have a checkbox to select them
            for i in _filtered_dict:
                if only_checkbox_for:
                    if only_checkbox_for==i['teacher']['code']:
                        i['cb'] = "<input type='checkbox' class='cb_all' name='cb' value='{}'>".format(i['id'], i['id'])
                else:
                    i['cb'] = "<input type='checkbox' class='cb_all' name='cb' value='{}'>".format(i['id'], i['id'])
        #order, if required, 2nd stage
        _template = table['template']
        column_number = check_value_in_form('order[0][column]', request.values)
        if column_number and _template[int(column_number)]['order_by'] and  callable(_template[int(column_number)]['order_by']):
            reverse = False if check_string_in_form('order[0][dir]', request.values) == 'desc' else True
            _filtered_dict = sorted(_filtered_dict, key= _template[int(column_number)]['order_by'], reverse=reverse)
    except Exception as e:
        log.error('could not prepare data for html : {}'.format(e))
        flash_plus('Er is een fout opgetreden en de tabel kan niet getoond worden.', e)
        _total_count = _filtered_list = 0
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
