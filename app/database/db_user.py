from flask import session
from flask_login import current_user
from app import login_manager
from app.database.models import User
from app.database import db_teacher, db_schedule, db_replacement


def filter(query_in):
    #If the logged in user is NOT administrator, display the data of the current user only
    if not current_user.is_at_least_admin:
        return query_in.filter(User.id==current_user.id)
    return query_in


# Set up user_loader
@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        user.teacher = db_teacher.db_teacher(code=user.username)
        user.in_schedule = not not db_schedule.db_schedule_list(teacher=user.teacher) if user.teacher else False
        user.in_replacement = not not db_replacement.replacement_list(id=user.teacher.id) if user.teacher else False

        teacher_ids = []
        if user.in_schedule:
            teacher_ids.append(user.teacher.id)
        if user.in_replacement:
            teacher_ids += db_replacement.replacement_list(user.teacher.id, ids_only=True)
        if teacher_ids:
            user.teacher_list = db_teacher.db_teacher_list(select=True, full_name=True, id_list=teacher_ids)

    return user


#Simulate a filter where the teacher has changed.
def default_grade_filter():
    teacher_found = db_teacher.db_teacher(code=current_user.username)
    teacher_in_schedule = not not db_schedule.db_schedule_list(teacher=teacher_found) if teacher_found else False
    if teacher_in_schedule:
        teacher_id = db_teacher.db_teacher(code=current_user.username.upper()).id
    else:
        teacher_id = db_teacher.db_teacher_list()[0].id
    session_set_grade_filter(teacher_id=teacher_id, day_hour='None', grade_id=-1, lesson_id=-1, changed_item='teacher')


def session_set_grade_filter(teacher_id=None, day_hour=None, grade_id=None, lesson_id=None, changed_item=None):
    if teacher_id:
        session['teacher_id'] = teacher_id
    if day_hour:
        session['day_hour'] = day_hour
    if grade_id:
        session['grade_id'] = grade_id
    if lesson_id:
        session['lesson_id'] = lesson_id
    if changed_item:
        session['change_id'] = changed_item


def session_get_grade_filter():
    return session['teacher_id'], session['day_hour'], session['grade_id'], session['lesson_id'], session['change_id']