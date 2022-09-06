from app import log, app
import sys, datetime, requests, json


# return a sorted list of all existing classes
def get_unique_klassen():
    try:
        # sdh_url = msettings.get_configuration_setting('sdh-base-url')
        # sdh_key = msettings.get_configuration_setting('sdh-api-key')
        sdh_url = app.config['SDH_URL']
        sdh_key = app.config['SDH_KEY']
        session = requests.Session()
        res = session.get(f'{sdh_url}/students?fields=klascode', headers={'x-api-key': sdh_key})
        if res.status_code == 200:
            data = res.json()
            if data['status']:
                sdh_klassen = sorted(set([v['klascode'] for v in data['data']]))
                return sdh_klassen
            else:
                log.error(f'{sys._getframe().f_code.co_name}: {data["data"]}')
        return None
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')


def get_teachers_info():
    try:
        # sdh_url = msettings.get_configuration_setting('sdh-base-url')
        # sdh_key = msettings.get_configuration_setting('sdh-api-key')

        sdh_url = app.config['SDH_URL']
        sdh_key = app.config['SDH_KEY']

        session = requests.Session()
        res = session.get(f'{sdh_url}/staffs?fields=code,naam,voornaam,geboortedatum,email,geslacht', headers={'x-api-key': sdh_key})
        if res.status_code == 200:
            data = res.json()
            if data['status']:
                return data['data']
            else:
                log.error(f'{sys._getframe().f_code.co_name}: {data["data"]}')
        return None
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')



def get_students_info():
    try:
        # sdh_url = msettings.get_configuration_setting('sdh-base-url')
        # sdh_key = msettings.get_configuration_setting('sdh-api-key')
        sdh_url = app.config['SDH_URL']
        sdh_key = app.config['SDH_KEY']


        session = requests.Session()
        res = session.get(f'{sdh_url}/students?fields=leerlingnummer,naam,voornaam,geboortedatum,geslacht,klascode', headers={'x-api-key': sdh_key})
        if res.status_code == 200:
            data = res.json()
            if data['status']:
                return data['data']
            else:
                log.error(f'{sys._getframe().f_code.co_name}: {data["data"]}')
        return None
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')





