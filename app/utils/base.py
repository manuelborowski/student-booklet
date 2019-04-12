# -*- coding: utf-8 -*-

import datetime
from flask import flash, request
from app import app

#This will make the variable 'academic_year' default available in all templates
@app.context_processor
def inject_academic_year():
    return dict(academic_year=get_academic_year())

def get_academic_year():
    now = datetime.datetime.now()
    reference = datetime.datetime(year=now.year, month=8, day=1)
    now_year = int(str(now.year)[2:4])
    if now < reference:
        year = (now_year - 1) * 100 + now_year
    else:
        year = now_year * 100 + now_year + 1
    return year


def filter_duplicates_out(keep_list, filter_list):
    keep_list.append(('disabled', '--------'))
    for i in filter_list:
        if not i in keep_list:
            keep_list.append(i)
    return keep_list

#It is possible to give an extra (exception) message
#The python UTF-8 string is encoded to html UTF-8
def flash_plus(message, e=None):
    if e:
        flash(('{}<br><br>Details:<br>{}'.format(message, e)))
    else:
        flash(('{}'.format(message)))

def button_save_pushed():
    return 'button' in request.form and request.form['button'] == 'save'

