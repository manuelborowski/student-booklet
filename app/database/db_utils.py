import datetime

from app import app, log
from app.database import db_setting
from app.database.models import SCHOOL

@app.context_processor
def inject_academic_year():
    return dict(academic_year=academic_year(), test_server=db_setting.get_global_setting_test_server())


def school():
    return SCHOOL.LYCEUM


def academic_year():
    now = datetime.datetime.now()
    if db_setting.get_global_setting_sim_dayhour_state():
        try:
            now = datetime.datetime.strptime(db_setting.get_global_setting_sim_dayhour(), '%d-%m-%Y %H:%M')
        except Exception as e:
            log.error('bad sim dayhour string : {}'.format(e))
    reference = datetime.datetime(year=now.year, month=8, day=1)
    now_year = int(str(now.year)[2:4])
    if now < reference:
        year = (now_year - 1) * 100 + now_year
    else:
        year = now_year * 100 + now_year + 1
    return year