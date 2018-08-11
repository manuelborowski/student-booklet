# -*- coding: utf-8 -*-
from wtforms.widgets.core import html_params
from wtforms.widgets import HTMLString
from wtforms import BooleanField
from flask import flash,  request, get_flashed_messages, jsonify, url_for
from flask_login import current_user
from sqlalchemy import or_
import time, datetime

from models import User, Settings, Teacher, Classmoment, Classgroup, Lesson
#from .forms import CategoryFilter, DeviceFilter, StatusFilter, SupplierFilter
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

def build_filter(table, paginate=True):
    #depending on the table, multiple joins are required to get the necessary data
    _model = table['model']
    _filters_enabled = table['filter']
    _template = table['template']
    _filtered_list = _model.query
    # if ('since' in  _filters_enabled or 'value' in _filters_enabled) and _model is not Purchase:
    #     _filtered_list = _filtered_list.join(Purchase)
    # if ('category' in _filters_enabled or 'device' in _filters_enabled) and _model is not Device:
    #     _filtered_list = _filtered_list.join(Device)
    # if 'supplier' in _filters_enabled and _model is not Supplier :
    #     _filtered_list = _filtered_list.join(Supplier)

    if 'query_filter' in table:
        _filtered_list = table['query_filter'](_filtered_list)

    _total_count = _filtered_list.count()

    _filter_forms = {}

    #Create the sql-request with the apropriate filters
    # if 'since' in _filters_enabled:
    #     date = check_date_in_form('date_after', request.values)
    #     if date:
    #         _filtered_list = _filtered_list.filter(Purchase.since >= Purchase.reverse_date(date))
    #     date = check_date_in_form('date_before', request.values)
    #     if date:
    #         _filtered_list = _filtered_list.filter(Purchase.since <= Purchase.reverse_date(date))
    # if 'value' in _filters_enabled:
    #     value = check_value_in_form('value_from', request.values)
    #     if value:
    #         _filtered_list = _filtered_list.filter(Purchase.value >= value)
    #     value = check_value_in_form('value_till', request.values)
    #     if value:
    #         _filtered_list = _filtered_list.filter(Purchase.value <= value)
    # if 'location' in _filters_enabled:
    #     value = check_string_in_form('room', request.values)
    #     if value:
    #         _filtered_list = _filtered_list.filter(Asset.location.contains(value))
    # if 'category' in _filters_enabled:
    #     _filter_forms['category'] = CategoryFilter()
    #     value = check_string_in_form('category', request.values)
    #     if value:
    #         _filtered_list = _filtered_list.filter(Device.category == value)
    # if 'status' in _filters_enabled:
    #     _filter_forms['status'] = StatusFilter()
    #     value = check_string_in_form('status', request.values)
    #     if value:
    #         _filtered_list = _filtered_list.filter(Asset.status == value)
    # if 'supplier' in _filters_enabled:
    #     _filter_forms['supplier'] = SupplierFilter()
    #     value = check_string_in_form('supplier', request.values)
    #     if value:
    #         _filtered_list = _filtered_list.filter(Supplier.name == value)
    # if 'device' in _filters_enabled:
    #     _filter_forms['device'] = DeviceFilter()
    #     value = check_string_in_form('device', request.values)
    #     if value:
    #         s = value.split('/')
    #         _filtered_list = _filtered_list.filter(Device.brand==s[0].strip(), Device.type==s[1].strip())

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
        # if Asset.name in column_list:
        #     search_constraints.append(Asset.name.like(search_value))
        # if Device.category in column_list:
        #     search_constraints.append(Device.category.like(search_value))
        # if Asset.location in column_list:
        #     search_constraints.append(Asset.location.like(search_value))
        # if Purchase.since in column_list:
        #     search_constraints.append(Purchase.since.like(search_date))
        # if Purchase.value in column_list:
        #     search_constraints.append(Purchase.value.like(search_value))
        # if Asset.qr_code in column_list:
        #     search_constraints.append(Asset.qr_code.like(search_value))
        # if Asset.status in column_list:
        #     search_constraints.append(Asset.status.like(search_value))
        # if Supplier.name in column_list:
        #     search_constraints.append(Supplier.name.like(search_value))
        # if Device.brand in column_list:
        #     search_constraints.append(Device.brand.like(search_value))
        #     search_constraints.append(Device.type.like(search_value))
        # if Asset.serial in column_list:
        #     search_constraints.append(Asset.serial.like(search_value))
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

    #order, if required
    column_number = check_value_in_form('order[0][column]', request.values)
    if column_number:
        column_name = check_string_in_form('columns[' + str(column_number) + '][data]', request.values)
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


def get_ajax_table(table):
    __filters_enabled,  _filter_forms, _filtered_list, _total_count, _filtered_count = build_filter(table)
    _filtered_dict = [i.ret_dict() for i in _filtered_list]
    for i in _filtered_dict:
        for h in table['href']:
            exec("i" + h['attribute'] + "= \"<a href=\\\"{}\\\">{}</a>\".format(url_for(" + h['route'] + ", id=i" + h['id'] + "), i" + h['attribute'] + ')')
        i['DT_RowId'] = i['id']
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
    teacher = Teacher.query.get(teacher_id)
    classmoment = None
    classgroup = None
    lesson = None

    if not changed_item:
        teacher = Teacher.query.distinct(Teacher.name).order_by(Teacher.name).first()
        changed_item = 'teacher'

    if changed_item == 'teacher':
        d, h = get_timeslot_from_current_time()
        dayhour_str = '{}/{}'.format(d,h)
        changed_item = 'dayhour'

    if changed_item == 'dayhour':
        #fetch classgroup from timetable
        d, h = Classmoment.decode_dayhour(dayhour_str)
        classmoment = Classmoment.query.join(Teacher).filter(Classmoment.day == d, Classmoment.hour == h, Teacher.id == teacher.id).first()
        if classmoment:
            classgroup = classmoment.classgroup
        else:
            classgroup = Classgroup.query.join(Classmoment).join(Teacher).filter(Teacher.id == teacher.id).distinct(Classgroup.name).order_by(Classgroup.name).first()
            if not classgroup:
                classgroup = Classgroup.query.distinct(Classgroup.name.order_by(Classgroup.name).first())
        changed_item = 'classgroup'

    if changed_item == 'classgroup':
        if classmoment:
            lesson = classmoment.lesson
        else:
            lesson = Lesson.query.join(Classmoment).join(Classgroup).filter(Classgroup.id == classgroup.id).distinct(Lesson.name).order_by(Lesson.name).first()
            if not lesson:
                lesson = Lesson.query.distinct(Lesson.name).order_by(Lesson.name).first()

    print(teacher,  classmoment, classgroup, lesson, dayhour_str)
    return teacher, classmoment, classgroup, lesson, dayhour_str
