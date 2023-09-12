from app import log, app, db
from app.database.models import SCHOOL, Teacher, Student
from app.database import db_classgroup
import sys, datetime, requests, json, base64
from zeep import Client


soap = Client(app.config["SS_API_URL"])

def __calc_academic_year():
    now = datetime.date.today()
    year = now.year - 2000
    if now.month > 8:
        academic_year = year  * 100 + year + 1
    else:
        academic_year = (year - 1)  * 100 + year
    return academic_year



SS_TEACHER_GROUPS = {
    'LeerkrachtenInstituut': SCHOOL.INSTITUUT,
    'LeerkrachtenMiddenschool': SCHOOL.MIDDENSCHOOL,
    'LeerkrachtenLyceum': SCHOOL.LYCEUM}


def import_lkr_from_ss():
    try:
        #import lkr from smartschool
        log.info(f"{sys._getframe().f_code.co_name}, START")
        ret = soap.service.getAllAccountsExtended(app.config["SS_API_KEY"], "leerkracht", "0")
        data = json.loads(ret)
        academic_year = __calc_academic_year()
        nbr_teachers = 0
        for teacher in data:
            for group in teacher["groups"]:
                if group["code"] in SS_TEACHER_GROUPS:
                    code = teacher["gebruikersnaam"].upper()
                    school = SS_TEACHER_GROUPS[group["code"]]
                    find_teacher = Teacher.query.filter(Teacher.code == code, Teacher.school == school).first()
                    if find_teacher:
                        find_teacher.first_name = teacher["voornaam"]
                        find_teacher.last_name = teacher["naam"]
                        find_teacher.academic_year = academic_year
                    if not find_teacher:
                        new_teacher = Teacher(first_name=teacher["voornaam"], last_name=teacher["naam"], code=code,
                                          academic_year=academic_year, school=school)
                        db.session.add(new_teacher)
                        nbr_teachers += 1
        db.session.commit()
        log.error(f'{sys._getframe().f_code.co_name}: {nbr_teachers} teachers imported')
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')

def __slice_list(list_in, slice_size):
    list_out = []
    idx = 0
    while idx < len(list_in):
        list_out.append(list_in[idx:idx + slice_size] if idx + slice_size < len(list_in) else list_in[idx::])
        idx += slice_size
    return list_out


def import_student_from_sdh(opaque=None, **kwargs):
    log.info(f"{sys._getframe().f_code.co_name}, START")
    try:
        # check for new, updated or deleted students
        sdh_key = app.config["SDH_KEY"]
        academic_year = __calc_academic_year()
        nbr_new_students = 0
        nbr_updated_students = 0
        klassen = {c.code: c for c in db_classgroup.db_classgroup_list()}
        res = requests.get(app.config["SDH_URL_STUDENT"], headers={'x-api-key': sdh_key})
        if res.status_code == 200:
            sdh_students = res.json()
            if sdh_students['status']:
                log.info(f'{sys._getframe().f_code.co_name}, retrieved {len(sdh_students["data"])} students from SDH')
                db_students = db.session.query(Student).all()
                db_leerlingnummer_to_student = {str(s.number): s for s in db_students}
                for sdh_student in sdh_students["data"]:
                    if sdh_student["klascode"] in klassen:
                        if sdh_student["leerlingnummer"] in db_leerlingnummer_to_student:
                            # check for changed rfid or classgroup
                            db_student = db_leerlingnummer_to_student[sdh_student["leerlingnummer"]]
                            db_student.first_name = sdh_student["voornaam"]
                            db_student.last_name = sdh_student["naam"]
                            db_student.academic_year = academic_year
                            db_student.photo = str(sdh_student["foto_id"])
                            db_student.classgroup = klassen[sdh_student["klascode"]]
                            nbr_updated_students += 1
                        else:
                            new_student = Student(first_name=sdh_student["voornaam"], last_name=sdh_student["naam"], number=sdh_student["leerlingnummer"],
                                                  academic_year=academic_year, classgroup=klassen[sdh_student["klascode"]], photo=str(sdh_student["foto_id"]))
                            db.session.add(new_student)
                            nbr_new_students += 1
                log.info(f"{sys._getframe().f_code.co_name}, {nbr_new_students} new students, {nbr_updated_students} updated from SDH")
                db.session.commit()
                db_students = db.session.query(Student).filter(Student.academic_year == academic_year).all()
                db_students_cache = {s.photo: s for s in db_students }
                foto_ids = [s.photo for s in db_students]
                sliced_photo_ids = __slice_list(foto_ids, 200)
                for slice in sliced_photo_ids:
                    res = requests.get(app.config["SDH_URL_FOTO"], params={"ids": ",".join(slice)}, headers={'x-api-key': sdh_key})
                    if res.status_code == 200:
                        sdh_photo_data = res.json()
                        if sdh_photo_data["status"]:
                            log.info(f'{sys._getframe().f_code.co_name}, retrieved {len(sdh_photo_data["data"])} photos from SDH')
                            for sdh_photo in sdh_photo_data["data"]:
                                id = sdh_photo["id"]
                                decoded_photo = base64.b64decode(sdh_photo["photo"].encode("ascii"))
                                db_student = db_students_cache[str(id)]
                                db_student.photoblob = decoded_photo
                        else:
                            log.info(f'{sys._getframe().f_code.co_name}, error retrieving photos from SDH, {sdh_photo_data["data"]}')
                    else:
                        log.error(f'{sys._getframe().f_code.co_name}: api call to {app.config["SDH_URL_FOTO"]} returned {res.status_code}')
                db.session.commit()
        log.info(f"{sys._getframe().f_code.co_name}, STOP")
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
    return True





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




