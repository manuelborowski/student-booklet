# -*- coding: utf-8 -*-
# app/auth/views.py

from flask import flash, redirect, render_template, url_for, request, session
from flask_login import login_required, login_user, logout_user, current_user

from .. import log, db, app
from . import auth
from forms import LoginForm
from ..models import User
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
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.is_local() and user.verify_password(form.password.data):
            login_user(user)
            log.info('LOCAL user {} logged in'.format(user.username))
            user.last_login = datetime.datetime.now()
            try:
                db.session.commit()
            except Exception as e:
                log.error('Could not save timestamp : {}'.format(e))
                flash('Fout in database : {}'.format(e))
                return redirect(url_for('auth.login'))
            # Ok, continue
            return redirect(url_for('overview.show'))
        else:
            flash('Ongeldige gebruikersnaam of paswoord')
            log.error("Invalid username/password")
    return render_template('auth/login.html', form=form, title='Login')

#OAUTH specific
@auth.route('/smartschool_profile/<string:token>', methods=['GET', 'POST'])
def smartschool_profile(token):
    # Step 3 : with the access_code, get the userinfo from SS
    resp = oauth.smartschool.get('fulluserinfo', token=json.loads(token))
    profile = resp.json()

    if 'error' in profile: #not good
        flash('Smartschool geeft een foutcode terug: {}'.format(profile['error']))
        log.error("OAUTH step 3 error : {}".format(profile['error']))
        return redirect(url_for('auth.login'))

    if profile['basisrol'] in SMARTSCHOOL_ALLOWED_BASE_ROLES:
        #Students are NOT allowed to log in
        user = User.query.filter_by(username=profile['username'], user_type=User.USER_TYPE.OAUTH).first()
        if not user:
            user = User(username=profile['username'], first_name=profile['name'], last_name=profile['surname'],
                        email=profile['email'], user_type=User.USER_TYPE.OAUTH)
            db.session.add(user)
            db.session.flush() #user.id is filled in
        user.last_login = datetime.datetime.now()
        login_user(user)
        log.info('OAUTH user {} logged in'.format(user.username))
        try:
            db.session.commit()
        except Exception as e:
            log.error('Could not save user : {}'.format(e))
            flash('Fout in database : {}'.format(e))
            return redirect(url_for('auth.login'))
        #Ok, continue
        return redirect(url_for('overview.show'))

    flash('Geen geldige smartschoolaccount, alleen leerkrachten, directie of personeel')
    log.error('Invalid smartschool account : {}'.format(profile['username']))
    return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    log.info('User logged out')
    logout_user()
    flash('U bent uitgelogd')
    return redirect(url_for('auth.login'))

