# -*- coding: utf-8 -*-
# app/asset/views.py

from flask import render_template, redirect, url_for, request, flash, send_file, session
from flask_login import login_required, current_user

#from .forms import AddForm, EditForm, ViewForm
from .. import db, log
from . import offence
from ..models import Offence, Type, Measure, Teacher, Classgroup, Lesson

from ..base import build_filter, get_ajax_table, get_setting_inc_index_asset_name
from ..tables_config import  tables_configuration
from ..documents import download_single_doc

import cStringIO, csv, re

from werkzeug.datastructures import FileStorage

#This route is called by an ajax call on the assets-page to populate the table.
@offence.route('/offence/data', methods=['GET', 'POST'])
@login_required
def source_data():
    return get_ajax_table(tables_configuration['offence'])

#show a list of assets
@offence.route('/offence', methods=['GET', 'POST'])
@login_required
def offences():
    #The following line is required only to build the filter-fields on the page.
    _filter, _filter_form, a,b, c = build_filter(tables_configuration['offence'])
    return render_template('base_multiple_items.html',
                           title='Opmerkingen',
                           filter=_filter, filter_form=_filter_form,
                           config = tables_configuration['offence'])

# #export a list of assets
# @asset.route('/asset/export', methods=['GET', 'POST'])
# @login_required
# def exportcsv():
#     #The following line is required only to build the filter-fields on the page.
#     __filters_enabled,  _filter_forms, _filtered_list, _total_count, _filtered_count = build_filter(tables_configuration['asset'])
#     csv_file = cStringIO.StringIO()
#     headers = [
#         'name',
#         'category',
#         'location',
#         'since',
#         'value',
#         'qr',
#         'status',
#         'supplier',
#         'brand',
#         'type',
#         'serial',
#         'power',
#         'ce',
#     ]
#
#     rows = []
#     for a in _filtered_list:
#         rows.append(
#             {
#                 'name' : a.name,
#                 'category' : a.purchase.device.category,
#                 'location' : a.location,
#                 'since' : a.purchase.since,
#                 'value' : a.purchase.value,
#                 'qr' : a.qr_code,
#                 'status' : a.status,
#                 'supplier' : a.purchase.supplier.name,
#                 'brand' : a.purchase.device.brand,
#                 'type' : a.purchase.device.type,
#                 'serial' : a.serial,
#                 'power' : a.purchase.device.power,
#                 'ce' : a.purchase.device.ce
#             }
#         )
#
#     writer = csv.DictWriter(csv_file, headers, delimiter=';')
#     writer.writeheader()
#     for r in rows:
#         writer.writerow(dict((k, v.encode('utf-8') if type(v) is unicode else v) for k, v in r.iteritems()))
#     csv_file.seek(0)
#     return send_file(csv_file, attachment_filename='assets.csv', as_attachment=True)
#
# #add a new asset
# @asset.route('/asset/add/<int:id>/<int:qr>', methods=['GET', 'POST'])
# @asset.route('/asset/add/<int:qr>', methods=['GET', 'POST'])
# @asset.route('/asset/add/<int:id>', methods=['GET', 'POST'])
# @asset.route('/asset/add', methods=['GET', 'POST'])
# @login_required
# def add(id=-1, qr=-1):
#     #qr_code can be inserted in 2 forms :
#     #regular number, e.g. 433
#     #complete url, e.g. http://blabla.com/qr/433.  If it contains http.*qr/, extract the number after last slash.
#     asset = Asset.query.filter_by(id=int(id)).first()
#     if asset:
#         if get_setting_inc_index_asset_name():
#             #the new name is the same as the old one, but the index is incremented
#             #if no index available, create default 001
#             nbr = re.search(r'\d+$', asset.name)
#             if nbr is None:
#                 asset.name = asset.name + '1'
#             else:
#                 idx = int(nbr.group()) + 1
#                 asset.name = asset.name[:-len(nbr.group())] + str(idx)
#         form = AddForm(obj=asset)
#         form.serial.data=''
#         #No idea why only these 2 fields need to be copied explicitly???
#         form.name.data = asset.name
#         form.location.data = asset.location
#     else:
#         form = AddForm()
#     del form.id # is not required here and makes validate_on_submit fail...
#     #Validate on the second pass only (when button 'Bewaar' is pushed)
#     if 'button' in request.form and request.form['button'] == 'Bewaar' and form.validate_on_submit():
#         asset = Asset(name=form.name.data,
#                         qr_code=form.qr_code.data,
#                         status=form.status.data,
#                         location=form.location.data,
#                         purchase=form.purchase.data,
#                         serial=form.serial.data)
#         db.session.add(asset)
#         db.session.commit()
#         db.session.refresh(asset)
#         session['asset_last_added'] = asset.id
#         log.info('add : {}'.format(asset.log()))
#         #flash(u'You have added asset {}').format(asset.name)
#         return redirect(url_for('asset.assets'))
#
#     form.qr_code.data=qr if qr > -1 else ''
#     return render_template('asset/asset.html', form=form, title='Voeg activa toe', role='add', route='asset.assets', subject='asset')
#
# #edit a asset
# @asset.route('/asset/edit/<int:id>', methods=['GET', 'POST'])
# @login_required
# def edit(id):
#     asset = Asset.query.get_or_404(id)
#     form = EditForm(obj=asset)
#     if form.validate_on_submit():
#         if request.form['button'] == 'Bewaar':
#             form.populate_obj(asset)
#             db.session.commit()
#             log.info('edit : {}'.format(asset.log()))
#             #flash'You have edited asset {}').format(asset.name)
#
#         return redirect(url_for('asset.assets'))
#
#     return render_template('asset/asset.html', form=form, title='Pas een activa aan', role='edit', subject='asset', route='asset.assets')
#
# #no login required
# @asset.route('/asset/view/<int:id>', methods=['GET', 'POST'])
# def view(id):
#     asset = Asset.query.get_or_404(id)
#     form = ViewForm(obj=asset)
#     form.since.data = asset.purchase.since
#     form.category.data = asset.purchase.device.category
#     form.value.data = asset.purchase.value
#     form.supplier.data = asset.purchase.supplier
#
#     form.brand.data = asset.purchase.device.brand
#     form.type.data  = asset.purchase.device.type
#     form.power.data = asset.purchase.device.power
#     form.ce.data  = asset.purchase.device.ce
#     form.risk_analysis.data = asset.purchase.device.risk_analysis
#     form.manual.data  = asset.purchase.device.manual
#     form.safety_information.data = asset.purchase.device.safety_information
#     form.photo.data = asset.purchase.device.photo
#
#     if form.validate_on_submit():
#         return redirect(url_for('asset.assets'))
#
#     return render_template('asset/asset.html', form=form, title='Bekijk een activa', role='view', subject='asset', route='asset.assets')
#
#
# #no login required
# @asset.route('/asset/qr/<string:qr>', methods=['GET', 'POST'])
# def view_via_qr(qr):
#     try:
#         asset = Asset.query.filter_by(qr_code=qr).first()
#         form = ViewForm(obj=asset)
#         form.since.data = asset.purchase.since
#         form.category.data = asset.purchase.device.category
#         form.value.data = asset.purchase.value
#         form.supplier.data = asset.purchase.supplier
#
#         form.brand.data = asset.purchase.device.brand
#         form.type.data  = asset.purchase.device.type
#         form.power.data = asset.purchase.device.power
#         form.ce.data  = asset.purchase.device.ce
#         form.risk_analysis.data = asset.purchase.device.risk_analysis
#         form.manual.data  = asset.purchase.device.manual
#         form.safety_information.data = asset.purchase.device.safety_information
#         form.photo.data = asset.purchase.device.photo
#     except:
#         #scanned a QR code which is not in the database yet, so it is assumed that a new asset is to be added
#         copy_from_asset_id = session['asset_last_added'] if 'asset_last_added' in session else -1
#         try:
#             if current_user.is_authenticated:
#                 return redirect(url_for('asset.add', id=copy_from_asset_id, qr=int(qr)))
#             else:
#                 return redirect(url_for('auth.login', redirect_url=url_for('asset.add', id=copy_from_asset_id, qr=int(qr))))
#         except:
#             flash('Ongeldige QR code')
#             return redirect(url_for('auth.login'))
#
#     return render_template('asset/asset.html', form=form, title='Bekijk een activa', role='view', subject='asset', route='asset.assets')
#
# #delete an asset
# @asset.route('/asset/delete/<int:id>', methods=['GET', 'POST'])
# @login_required
# def delete(id):
#     asset = Asset.query.get_or_404(id)
#     log.info('delete : {}'.format(asset.log()))
#     db.session.delete(asset)
#     db.session.commit()
#     #flash('You have successfully deleted the asset.')
#
#     return redirect(url_for('asset.assets'))
#
# #download a ... file
# @asset.route('/asset/download', methods=['GET', 'POST'])
# @login_required
# def download():
#     try:
#         return download_single_doc(request)
#     except Exception as e:
#         flash('Kan niet downloaden  ')
#     return ('', 204)
