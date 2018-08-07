# -*- coding: utf-8 -*-

from models import User
import user.extra_filtering
from floating_menu import default_menu_config

tables_configuration = {
    # 'asset' : {
    #     'model' : Asset,
    #     'title' : 'activa',
    #     'route' : 'asset.assets',
    #     'subject' :'asset',
    #     'delete_message' : '',
    #     'template' : [{'name': 'Naam', 'data':'name', 'order_by': Asset.name},
    #                   {'name': 'Categorie', 'data':'purchase.device.category', 'order_by': Device.category},
    #                   {'name': 'Locatie', 'data':'location', 'order_by': Asset.location},
    #                   {'name': 'Datum', 'data':'purchase.since', 'order_by': Purchase.since},
    #                   {'name': 'Bedrag', 'data':'purchase.value', 'order_by': Purchase.value},
    #                   {'name': 'QR', 'data':'qr_code', 'order_by': Asset.qr_code},
    #                   {'name': 'Status', 'data':'status', 'order_by': Asset.status},
    #                   {'name': 'Leverancier', 'data':'purchase.supplier.name', 'order_by': Supplier.name},
    #                   {'name': 'Toestel', 'data':'purchase.device.brandtype', 'order_by': Device.brand},
    #                   {'name': 'SerieNr', 'data': 'serial', 'order_by': Asset.serial}],
    #     'filter' :  ['since', 'value', 'location', 'category', 'status', 'supplier', 'device'],
    #     'href': [{'attribute': '["name"]', 'route': '"asset.view"', 'id': '["id"]'},
    #              {'attribute': '["purchase"]["since"]', 'route': '"purchase.view"', 'id': '["purchase"]["id"]'},
    #              {'attribute': '["purchase"]["supplier"]["name"]', 'route': '"supplier.view"', 'id': '["purchase"]["supplier"]["id"]'},
    #              {'attribute': '["purchase"]["device"]["brandtype"]', 'route': '"device.view"', 'id': '["purchase"]["device"]["id"]'}
    #              ],
    #     'floating_menu' : default_menu_config,
    #     'export' : 'asset.exportcsv',
    # },
    'user': {
        'model': User,
        'title' : 'gebruiker',
        'route' : 'user.users',
        'subject' :'user',
        'delete_message' : '',
        'template': [
            {'name': 'Gebruikersnaam', 'data': 'username', 'order_by': User.username},
            {'name': 'Voornaam', 'data': 'first_name', 'order_by': User.first_name},
            {'name': 'Naam', 'data': 'last_name', 'order_by': User.last_name},
            {'name': 'Email', 'data': 'email', 'order_by': User.email},
            {'name': 'Is admin', 'data': 'is_admin', 'order_by': User.is_admin},],
        'filter': [],
        'href': [{'attribute': '["username"]', 'route': '"user.view"', 'id': '["id"]'},
                 ],
        'floating_menu' : default_menu_config,
        'query_filter' : user.extra_filtering.filter,
    }
}

