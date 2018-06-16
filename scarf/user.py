import re
import string
from scarf import app
from flask import redirect, url_for, render_template, session, request, flash
from core import redirect_back, SiteUser, NoUser, new_user, AuthFail, check_email
from main import PageData
import logging

import config
app.secret_key = config.SECRETKEY

BANNED = ['.*\.pl$',
          '.*\.ru$',
          '.*\.ovh$',
          '.*servicesp.bid$',
          '.*@mailtomee.com$',
          '.*\.linuxpl.eu$',
          '.*@vam2006.eu$',
          '.*@eisfeld-gebaeudereinigung.de$',
          '.*@salonyfryzjerskie.info$']

logger = logging.getLogger(__name__)

def check_new_user(request, nopass=False):
    ret = True
    try:
        user = SiteUser.create(request.form['username'])
        flash("User already exists!")
        ret = False
    except NoUser:
        if check_email(request.form['email']):
            flash("You may not create multiple users with the same email address.")
            return False

        valid = string.ascii_letters + string.digits + ' '
        for c in request.form['username']:
            if c not in valid:
                flash("Invalid character in username: " + c)
                ret = False

        if not nopass:
            pass1 = request.form['password']
            pass2 = request.form['password2']

            if pass1 != pass2:
                flash("The passwords entered don't match.")
                ret = False
            else:
                if len(pass1) < 6:
                    flash("Your password is too short, it must be at least 6 characters")
                    ret = False

        for regex in BANNED:
            if re.match(regex, request.form['email']):
                flash("Fuck you spammer")
                logger.info('Banned email address rejected: {}'.format(request.form['email']))
                ret = False

        if not re.match("[^@]+@[^@]+\.[^@]+", request.form['email']):
            flash("Invalid email address")
            ret = False

    return ret

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            user = SiteUser.create(request.form['username'])
        except NoUser as e:
            flash('Login unsuccessful.')
            return redirect_back(url_for('index'))

        try:
            user.authenticate(request.form['password'])
        except (NoUser, AuthFail) as e:
            if user.accesslevel is 0:
                flash('Your account has been banned')
                session.pop('username', None)
            else:
                flash('Login unsuccessful.')
            return redirect_back(url_for('index'))

        user.seen()

        session['username'] = user.username
        session.permanent = True
        flash('You were successfully logged in')

        if not request.args.get('index'):
            return redirect_back(url_for('index'))
        else:
            return redirect(url_for('index'))

    return redirect(url_for('error'))

@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    pd = PageData();
    pd.title = "New User"

    if 'username' in session:
        flash('You are already logged in.')
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            if not check_new_user(request):
                pd.username = request.form['username']
                pd.email = request.form['email']
                return render_template('new_user.html', pd=pd)

            if not new_user(request.form['username'], request.form['password'], request.form['email'], request.remote_addr):
                return render_template('error.html', pd=pd)

            try:
                user = SiteUser.create(request.form['username'])
                user.authenticate(request.form['password'])
                session['username'] = user.username
            except (NoUser, AuthFail):
                return render_template('error.html', pd=pd)

            flash('Welcome ' + request.form['username'])
            return redirect(url_for('index'))

        return render_template('new_user.html', pd=pd)

@app.route('/logout')
def logout():
    for key in session.keys():
        if 'facebook' not in key: 
            session.pop(key, None) 

    flash('You were successfully logged out')

    if not request.args.get('index'):
        return redirect_back(url_for('index'))
    else:
        return redirect(url_for('index'))
