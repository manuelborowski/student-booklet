# -*- coding: utf-8 -*-

from flask import flash, request


#This will make the variable 'academic_year' default available in all templates


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

