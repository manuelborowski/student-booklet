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
