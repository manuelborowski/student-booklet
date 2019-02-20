# -*- coding: utf-8 -*-
# app/auth/views.py

from flask import redirect, render_template, url_for, request
from flask_login import login_required, login_user, logout_user
from sqlalchemy import func

from .. import log, db, app
from . import auth
from .forms import LoginForm
from ..models import User
from ..base import flash_plus
import datetime, json
from authlib.flask.client import OAuth

oauth = OAuth(app)
smartschool = oauth.register('smartschool')

SMARTSCHOOL_ALLOWED_BASE_ROLES = [
    'Andere',
    'Leerkracht',
    'Directie'
]

@auth.route('/', methods=['GET', 'POST'])
def login():
    if 'smartschool' in request.args: #smartschool button is pushed
        #Step 1 : go to smartschool so that the user can log in with smartschool credentials
        redirect_uri = url_for('auth.login', _external=True)
        return oauth.smartschool.authorize_redirect(redirect_uri)

    if 'code' in request.args: #received a request with a OAUTH code
        #Step 2 : with the code from smartschool, fetch the access_token from smartschool
        token = oauth.smartschool.authorize_access_token()
        return redirect(url_for('auth.smartschool_profile', token=json.dumps(token)))

    form = LoginForm()
    if form.validate_on_submit():
        # check whether user exists in the database and whether
        # the password entered matches the password in the database
        user = User.query.filter_by(username=func.binary(form.username.data)).first()
        if user is not None and user.is_local and user.verify_password(form.password.data):
            login_user(user)
            log.info(u'LOCAL user {} logged in'.format(user.username))
            user.last_login = datetime.datetime.now()
            try:
                db.session.commit()
            except Exception as e:
                log.error(u'Could not save timestamp : {}'.format(e))
                flash_plus(u'Fout in database', e)
                return redirect(url_for('auth.login'))
            # Ok, continue
            return redirect(url_for('grade.show'))
        else:
            flash_plus(u'Ongeldige gebruikersnaam of paswoord')
            log.error(u'Invalid username/password')
    return render_template('auth/login.html', form=form, title='Login')

#OAUTH specific
@auth.route('/smartschool_profile/<string:token>', methods=['GET', 'POST'])
def smartschool_profile(token):
    # Step 3 : with the access_code, get the userinfo from SS
    resp = oauth.smartschool.get('fulluserinfo', token=json.loads(token))
    profile = resp.json()

    print(profile)

    if  not 'username' in profile: #not good
        flash_plus(u'Smartschool geeft een foutcode terug: {}'.format(profile['error']))
        log.error(u'OAUTH step 3 error : {}'.format(profile['error']))
        return redirect(url_for('auth.login'))

    if profile['basisrol'] in SMARTSCHOOL_ALLOWED_BASE_ROLES:
        #Students are NOT allowed to log in
        user = User.query.filter_by(username=func.binary(profile['username']), user_type=User.USER_TYPE.OAUTH).first()
        if user:
            user.first_name=profile['name']
            user.last_name=profile['surname']
            user.email=profile['email']
        else:
            user = User(username=profile['username'], first_name=profile['name'], last_name=profile['surname'],
                        email=profile['email'], user_type=User.USER_TYPE.OAUTH, level=User.LEVEL.USER)
            db.session.add(user)
            db.session.flush() #user.id is filled in
        user.last_login = datetime.datetime.now()
        login_user(user)
        log.info(u'OAUTH user {} logged in'.format(user.username))
        try:
            db.session.commit()
        except Exception as e:
            log.error(u'Could not save user : {}'.format(e))
            flash_plus(u'Fout in database', e)
            return redirect(url_for('auth.login'))
        #Ok, continue
        return redirect(url_for('grade.show'))

    flash_plus(u'Geen geldige smartschoolaccount, alleen leerkrachten, directie of personeel')
    log.error(u'Invalid smartschool account : {}'.format(profile['username']))
    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    log.info(u'User logged out')
    logout_user()
    #flash(u'U bent uitgelogd')
    return redirect(url_for('auth.login'))

