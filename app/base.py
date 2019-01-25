# -*- coding: utf-8 -*-
from wtforms.widgets.core import html_params
from wtforms.widgets import HTMLString
from wtforms import BooleanField
from flask import flash,  request, get_flashed_messages, jsonify, url_for
from flask_login import current_user
from sqlalchemy import or_, func
import time, datetime
from operator import getitem, attrgetter
from toolz import unique

from models import User, Settings, Teacher, Classmoment, Classgroup, Lesson, Student, Offence, Measure, Type, ExtraMeasure
from .forms import ClassgroupFilter, TeacherFilter
from . import log

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
        except:
            flash('Verkeerd datumformaat, moet in de vorm zijn : d-m-y')
    return ''

def check_value_in_form(value_key, form):
    if value_key in form and form[value_key] != '':
        try:
            float(form[value_key])
            return form[value_key]
        except:
            flash('Verkeerde getal notatie')
    return ''

def check_string_in_form(value_key, form):
    if value_key in form and form[value_key] != '':
        try:
            str(form[value_key])
            return form[value_key]
        except:
            flash('Verkeerde tekst notatie')
    return ''

def build_filter_and_filter_data(table, paginate=True):
    #depending on the table, multiple joins are required to get the necessary data
    _model = table['model']
    _filters_enabled = table['filter']
    _template = table['template']
    _filtered_list = _model.query

    if _model is Offence:
        _filtered_list = _filtered_list.join(Student)
        _filtered_list = _filtered_list.join(Classgroup)
        _filtered_list = _filtered_list.join(Teacher)
        _filtered_list = _filtered_list.join(Lesson)

    if _model is ExtraMeasure:
        _filtered_list = _filtered_list.join(Offence)
        _filtered_list = _filtered_list.join(Student)
        _filtered_list = _filtered_list.join(Classgroup)
        _filtered_list = _filtered_list.join(Teacher)
        _filtered_list = _filtered_list.join(Lesson)



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
            _filtered_list = _filtered_list.filter(Offence.timestamp >= Offence.reverse_date(date))
        date = check_date_in_form('date_before', request.values)
        if date:
            _filtered_list = _filtered_list.filter(Offence.timestamp <= Offence.reverse_date(date))

    if 'teacher' in _filters_enabled:
        _filter_forms['teacher'] = TeacherFilter()
        value = check_value_in_form('teacher', request.values)
        if value and int(value) > -1:
            _filtered_list = _filtered_list.filter(Teacher.id == value)

    if 'classgroup' in _filters_enabled:
        _filter_forms['classgroup'] = ClassgroupFilter()
        value = check_value_in_form('classgroup', request.values)
        if value and int(value) > -1:
            _filtered_list = _filtered_list.filter(Classgroup.id == value)

    if 'reviewed' in _filters_enabled:
        value = check_string_in_form('reviewed', request.values)
        if value == 'true':
            _filtered_list = _filtered_list.filter(Offence.reviewed==True, Offence.measure_id != None).join(ExtraMeasure)
        elif value == 'false' or value == '': #default
            _filtered_list = _filtered_list.filter(Offence.reviewed==False)


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
        if Classgroup.name in column_list:
            search_constraints.append(Classgroup.name.like(search_value))
        if Lesson.name in column_list:
            search_constraints.append(Lesson.name.like(search_value))
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

    # #order, if required, 2nd stage
    _template = table['template']
    column_number = check_value_in_form('order[0][column]', request.values)
    if column_number and _template[int(column_number)]['order_by'] and  callable(_template[int(column_number)]['order_by']):
        reverse = False if check_string_in_form('order[0][dir]', request.values) == 'desc' else True
        _filtered_dict = sorted(_filtered_dict, key= _template[int(column_number)]['order_by'], reverse=reverse)

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
    return jsonify(output)

######################################################################################################
###                                       Handle settings
######################################################################################################

from . import db

#return : found, value
# found : if True, setting was found else not
# value ; if setting was found, returns the value
def get_setting(name, id=-1):
    try:
        setting = Settings.query.filter_by(name=name, user_id=id if id > -1 else current_user.id).first()
        if setting.type== Settings.SETTING_TYPE.E_INT:
            value = int(setting.value)
        elif setting.type == Settings.SETTING_TYPE.E_FLOAT:
            value = float(setting.value)
        elif setting.type == Settings.SETTING_TYPE.E_BOOL:
            value = True if setting.value == 'True' else False
        else:
            value = setting.value
    except:
        return False, ''
    return True, value

def add_setting(name, value, type, id=-1):
    setting = Settings(name=name, value=str(value), type=type, user_id=id if id >-1 else current_user.id)
    db.session.add(setting)
    db.session.commit()
    log.info('add : {}'.format(setting.log()))
    return True

def set_setting(name, value, id=-1):
    try:
        setting = Settings.query.filter_by(name=name, user_id=id if id > -1 else current_user.id).first()
        setting.value = value
        db.session.commit()
    except:
        return False
    return True

def get_setting_inc_index_asset_name():
    found, value = get_setting('inc_index_asset_name')
    if found: return value
    add_setting('inc_index_asset_name', True, Settings.SETTING_TYPE.E_BOOL)
    return True

def set_setting_inc_index_asset_name(value):
    return set_setting('inc_index_asset_name', str(value))

def get_setting_copy_from_last_add():
    found, value = get_setting('copy_from_last_add')
    if found: return value
    add_setting('copy_from_last_add', True, Settings.SETTING_TYPE.E_BOOL)
    return True

def set_setting_copy_from_last_add(value):
    return set_setting('copy_from_last_add', str(value))

def get_setting_simulate_dayhour():
    found, value = get_setting('simulate_dayhour')
    if found: return value
    add_setting('simulate_dayhour', '0/0', Settings.SETTING_TYPE.E_STRING)
    return '0/0'

def set_setting_simulate_dayhour(value):
    return set_setting('simulate_dayhour', value)

def get_global_setting_current_schoolyear():
    found, value = get_setting('current_schoolyear', 1)
    if found: return value
    add_setting('current_schoolyear', '1718', Settings.SETTING_TYPE.E_STRING, 1)
    return '1718'

def set_global_setting_current_schoolyear(value):
    return set_setting('current_schoolyear', str(value), 1)

######################################################################################################
###  Overview : select appropriate classgroup e.d.
######################################################################################################

def get_timeslot_from_current_time():
    TT = [
        (8*60+30,  8*60+30+50,  1),   #first hour : 8:30 till 9:20
        (9*60+20,  9*60+20+50,  2),
        (10*60+25, 10*60+25+50, 3),
        (11*60+15, 11*60+15+50, 4),
        (12*60+5,  12*60+5+55,  5),
        (13*60+0,  13*60+0+50,  6),
        (13*60+50, 13*60+50+50, 7),
        (14*60+55, 15*60+55+50, 8),
        (15*60+45, 15*60+45+50, 9),
    ]

    TT_W = [
        (8*60+30,  8*60+30+50,  1),   #first hour : 8:30 till 9:20
        (9*60+20,  9*60+20+50,  2),
        (10*60+20, 10*60+20+50, 3),
        (11*60+10, 11*60+10+50, 4),
    ]

    simulate_dayhour = get_setting_simulate_dayhour()
    if simulate_dayhour != '0/0':
        return Classmoment.decode_dayhour(simulate_dayhour)

    now = datetime.datetime.now()
    day = now.weekday()+1
    if day > 5: return 1, 1 #no school, return monday, first hour
    tt = TT_W if day == 3 else TT
    m = now.hour * 60 + now.minute
    for t in tt:
        if m >= t[0] and m < t[1]: return day, t[2]
    return 1, 1 #not found, return monday, first hour



def filter_overview(teacher_id, dayhour_str, classgroup_id, lesson_id, changed_item=None):
    #filter on teacher, timeslot , classgroup and lesson
    #priority is as follows:
    #- if teacher is changed: determine timeslot from current time and find classgroup and lesson from timetable
    #- if timeslot is changed: from teacher and timeslot determine classgroup and lesson from timetable
    #                             If this does not work, pick first classgroup for that teacher
    #- if classgroup is changed : from teacher, timeslot and classgroup, try to determine lesson from timetable.
    #                             If this does not work, pick first available lesson for that classgroup
    #- if lesson is changed : go with the flow... :-)
    teacher = None
    classgroup = None
    lesson = None
    d = 0
    h = 0

    if changed_item:
        teacher = Teacher.query.get(teacher_id)
        classgroup = Classgroup.query.get(classgroup_id)
        lesson = Lesson.query.get(lesson_id)
        d, h = Classmoment.decode_dayhour(dayhour_str)
    else:
        teacher = Teacher.query.distinct(Teacher.code).order_by(Teacher.code).first()
        changed_item = 'teacher'

    if changed_item == 'teacher':
        d, h = get_timeslot_from_current_time()
        #if default day and hour (1, 1) is returned, try to find the first avaible lesmoment for given teacher
        classmoment = Classmoment.query.join(Teacher).filter(Teacher.id == teacher.id).order_by(Classmoment.day, Classmoment.hour).first()
        if classmoment:
            d = classmoment.day
            h = classmoment.hour
        #dayhour_str = '{}/{}'.format(d,h)
        changed_item = 'dayhour'

    if changed_item == 'dayhour':
        #fetch classgroup from timetable
        classmoment = Classmoment.query.join(Teacher).filter(Classmoment.day == d, Classmoment.hour == h, Teacher.id == teacher.id).first()
        if classmoment:
            #the classmoment points to a single teacher, classgroup and lesson
            print(classmoment)
            return classmoment
        # find the first classgroup, teached by given teacher
        classgroup = Classgroup.query.join(Classmoment).join(Teacher).filter(Teacher.id == teacher.id).distinct(Classgroup.name).order_by(Classgroup.name).first()
        if not classgroup:
            #just pick the first classgroup from all classgroups
            classgroup = Classgroup.query.distinct(Classgroup.name).order_by(Classgroup.name).first()
        changed_item = 'classgroup'

    if changed_item == 'classgroup':
        #find the first lesson, taken by given classgroup
        lesson = Lesson.query.join(Classmoment).join(Classgroup).join(Teacher).filter(Classgroup.id == classgroup.id, Teacher.id == teacher.id)\
                .distinct(Lesson.name).order_by(Lesson.name).first()
        if not lesson:
            #just pick the first lesson
            lesson = Lesson.query.distinct(Lesson.name).order_by(Lesson.name).first()

    #create a dummy classmoment
    classmoment = Classmoment(day=d, hour=h, schoolyear = get_global_setting_current_schoolyear(), teacher=teacher, lesson=lesson, classgroup=classgroup)
    return classmoment

def filter_duplicates_out(in_list):
    out_list = []
    added = set()
    for val in in_list:
        if not val in added:
            out_list.append(val)
            added.add(val)
    return out_list