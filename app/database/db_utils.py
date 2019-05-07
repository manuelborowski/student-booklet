import datetime

from app import app, log
from app.database import db_setting
from app.database.db_setting import get_global_setting_sim_dayhour_state, get_global_setting_sim_dayhour
from app.database.models import SCHOOL

@app.context_processor
def inject_information():
    sim_dayhour = None
    if db_setting.get_global_setting_sim_dayhour_state():
        try:
            sim_dayhour = db_setting.get_global_setting_sim_dayhour()
        except Exception as e:
            log.error('bad sim dayhour string : {}'.format(e))
    return dict(academic_year=academic_year(), test_server=db_setting.get_global_setting_test_server(), sim_dayhour=sim_dayhour)


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


TT = [
    (0, 8 * 60 + 30, 0),  # timeslot 9, of the previous day
    (8 * 60 + 30, 8 * 60 + 30 + 50, 1),  # first hour : 8:30 till 9:20
    (9 * 60 + 20, 9 * 60 + 20 + 50 + 15, 2),  # the break counts as timeslot 2
    (10 * 60 + 25, 10 * 60 + 25 + 50, 3),
    (11 * 60 + 15, 11 * 60 + 15 + 50, 4),
    (12 * 60 + 5, 12 * 60 + 5 + 55, 5),
    (13 * 60 + 0, 13 * 60 + 0 + 50, 6),
    (13 * 60 + 50, 13 * 60 + 50 + 50 + 15, 7),  # the break counts as timeslot 7
    (14 * 60 + 55, 14 * 60 + 55 + 50, 8),
    (15 * 60 + 45, 24 * 60, 9),  # the whole evening as timeslot 9
]

TT_W = [
    (0, 8 * 60 + 30, 0),  # timeslot 9 of the previous day
    (8 * 60 + 30, 8 * 60 + 30 + 50, 1),  # first hour : 8:30 till 9:20
    (9 * 60 + 20, 9 * 60 + 20 + 50 + 10, 2),  # the break counts as timeslot 2
    (10 * 60 + 20, 10 * 60 + 20 + 50, 3),
    (11 * 60 + 10, 24 * 60, 4),  # the whole evening count as timeslot 4
]

def time_to_timeslot(time=None, include_zero_hour=False):
    if time:
        now = time
    else:
        now = datetime.datetime.now()
        if get_global_setting_sim_dayhour_state():
            try:
                now = datetime.datetime.strptime(get_global_setting_sim_dayhour(), '%d-%m-%Y %H:%M')
            except Exception as e:
                log.error('bad sim dayhour string : {}'.format(e))
    day = now.weekday()+1
    m = now.hour * 60 + now.minute

    tt = TT_W if day == 3 else TT
    d = h = 1
    if day > 5 and not include_zero_hour: #no school, return friday last hour
        d = 5
        h = 9
    else:
        i = 99
        for t in tt:
            if t[0] <= m < t[1]:
                i = t[2]
                break
        if i == 99: #not found
            d = h = 1
        elif i == 0 and not include_zero_hour: #now is before 8:30 in the morning
            d = day - 1
            h = 9
            if d < 1:
                d = 5
                h = 9
        else: #now is after 8:30 in the morning
            h = i
            d = day
    return d, h

def timeslot_to_time(hour, day=None):
    h = 8
    m = 30
    for t in TT:
        if t[2] == hour:
            time = t[0]
            h = time // 60
            m = time % 60
            break
    return h, m
