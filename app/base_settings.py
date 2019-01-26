from flask_login import current_user
from models import Settings
from . import log
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
