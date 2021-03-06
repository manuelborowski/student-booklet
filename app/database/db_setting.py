from flask_login import current_user
from app.database.models import Settings
from app import log
from app import db

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

def get_global_setting_sim_dayhour():
    found, value = get_setting('simulate_dayhour', 1)
    if found: return value
    add_setting('simulate_dayhour', '01-01-2019 14:10', Settings.SETTING_TYPE.E_STRING, 1)
    return '01-01-2019 14:10'

def set_global_setting_sim_dayhour(value):
    return set_setting('simulate_dayhour', value, 1)

def get_global_setting_sim_dayhour_state():
    found, value = get_setting('simulate_dayhour_state', 1)
    if found: return value
    add_setting('simulate_dayhour_state', False, Settings.SETTING_TYPE.E_BOOL, 1)
    return False

def set_global_setting_sim_dayhour_state(value):
    return set_setting('simulate_dayhour_state', str(value), 1)

def get_global_setting_current_academic_year():
    found, value = get_setting('current_academic_year', 1)
    if found: return value
    add_setting('current_academic_year', '1718', Settings.SETTING_TYPE.E_STRING, 1)
    return '1718'

def set_global_setting_current_academic_year(value):
    return set_setting('current_academic_year', str(value), 1)

def get_global_setting_test_server():
    found, value = get_setting('test_server', 1)
    if found: return value
    add_setting('test_server', False, Settings.SETTING_TYPE.E_BOOL, 1)
    return False

def set_global_setting_help_url(value):
    return set_setting('help_url', str(value), 1)

def get_global_setting_help_url():
    found, value = get_setting('help_url', 1)
    if found: return value
    add_setting('help_url', '', Settings.SETTING_TYPE.E_STRING, 1)
    return ''

