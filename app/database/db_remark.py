import datetime
from app import db
from app.utils import utils
from app.database.models import Remark, Student, ExtraMeasure

# Per student, get all remarks which are not reviewed yet (review==False) and order by date (oldest first)
# Take the first remark off the list, add to r_match, and calculate last_date, i.e. timestamp + 30 (or +7)=> sliding window
# Iterate over the remaining remarks and add to r_match when its timestamp falls in the window, break if there are
# no remarks anymore or timestamp falls outside the window
# If the number of remarks in r_match >=5 (or 3), add the list of remarks to match_temp
# ELSE add the first remark to r_temp and copy it to r_match
# Remove these remarks in r_match from the original list
# Repeat for this student to check if there are more matches.  If so, add the remarks to match_temp or r_temp
# If all remarks of this student are checked, add all remark-lists in r_temp to matched_remarks, together with the student
# AND add the remaining remarks to non_matched_remarks

# From non_matched_remarks, filter out the remarks that cannot participate in a future match because it timestamps are too old
# Take the newest remark in the list and calculate the first_date, i.e. timestamp - 30
# Iterate over the list, from old to new, and mark an remark as REVIEWED if its timestamp is older then first_date

dummy_extra_match = {'id': -1, 'note': ''}

MAX_REMARKS_PER_MONTH = 5
MAX_REMARKS_PER_WEEK = 3

match_periods = [
    (MAX_REMARKS_PER_MONTH, lambda i: (i.timestamp + datetime.timedelta(days=29)).replace(hour=23, minute=59)),
    (MAX_REMARKS_PER_WEEK, lambda i: (i.timestamp + datetime.timedelta(days=6)).replace(hour=23, minute=59)),
]


def db_filter_remarks_to_be_reviewed(academic_year, test=False, commit=True):
    q = db.session.query(Student).join(Remark).filter(Remark.reviewed == False, Remark.school == utils.school(), Remark.academic_year == academic_year)
    if test:
        q = q.filter(Remark.test == True)
    students = q.distinct(Remark.student_id).order_by(Student.last_name, Student.first_name).all()
    matched_remarks = []
    non_matched_remarks = []
    reviewed_remarks = []
    match_id = 0
    for s in students:
        match_temp = []
        q = Remark.query.filter(Remark.reviewed == False, Remark.student == s, Remark.school == utils.school(), Remark.academic_year == academic_year)
        if test:
            q = q.filter(Remark.test == True)
        remarks = q.order_by(Remark.timestamp).all()
        # First, try to find remarks in a period of 30 days, then in a period of 7 days
        for max_remarks, calculate_last_date in match_periods:
            r_match = []  # temporary to store remarks in the period
            r_temp = []
            while remarks:
                r_first = remarks.pop(0)
                r_match.append(r_first)
                last_date = calculate_last_date(r_first)
                for r in remarks:
                    if r.timestamp <= last_date:
                        r_match.append(r)
                    else:
                        break
                if len(r_match) >= max_remarks:
                    extra_measure = r_match[0].extra_measure if r_match[0].extra_measure else dummy_extra_match
                    match_temp.append((match_id, extra_measure, r_match))
                    match_id += 1
                    del remarks[:len(r_match) - 1]
                else:
                    r_temp.append(r_first)  # no match, store for later use
                r_match = []
            remarks = r_temp
        non_matched_remarks += remarks
        if match_temp:
            matched_remarks.append((s, match_temp))
        # check if some remarks need their reviewed_flag set to TRUE
        if remarks:
            first_date = (remarks[-1].timestamp - datetime.timedelta(days=30)).replace(hour=0, minute=1)
            for r in remarks:
                if r.timestamp < first_date:
                    r.reviewed_flag = True
                    r2 = Remark.query.get(r.id)
                    r2.reviewed = True
                    reviewed_remarks.append(r)
    for r in reviewed_remarks:
        non_matched_remarks.remove(r)
    if commit:
        db.session.commit()
    return matched_remarks, non_matched_remarks


def db_add_extra_measure(rid_list, em, commit=True):
    r = Remark.query.get(rid_list[0])
    if r.extra_measure is not None:
        r.extra_measure.note = em
    else:
        extra_measure = ExtraMeasure(note=em)
        r.first_remark = True
        db.session.add(extra_measure)
        for rid in rid_list:
            r = Remark.query.get(rid)
            r.extra_measure = extra_measure
    if commit:
        db.session.commit()


def db_tag_remarks_as_reviewed(commit=True):
    remarks = Remark.query.filter(Remark.extra_measure_id != None, Remark.reviewed == False).all()
    for r in remarks:
        r.reviewed = True
    if commit:
        db.session.commit()
