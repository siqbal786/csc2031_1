# IMPORTS
from flask import Blueprint, render_template, flash, redirect, url_for, session
from markupsafe import Markup

from app import db
from models import User
from users.forms import RegisterForm, LoginForm, PasswordForm
from flask_login import login_user, logout_user, login_required, current_user

# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')


# VIEWS
# view registration
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # create signup form object
    form = RegisterForm()

    # if request method is POST or form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # if this returns a user, then the email already exists in database

        # if email already exists redirect user back to signup page with error message so user can try again
        if user:
            flash('Email address already exists')
            return render_template('users/register.html', form=form)

        # create a new user with the form data
        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        dob=form.dob.data,
                        postcode=form.postcode.data,
                        phone=form.phone.data,
                        password=form.password.data,
                        role='user')

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        session['email'] = new_user.email

        # sends user to setup_2fa
        return redirect(url_for('users.setup_2fa'))
    # if request method is GET or form not valid re-render signup page
    return render_template('users/register.html', form=form)


# view user login
@users_blueprint.route('/login', methods= ['GET', 'POST'])
def login():
    form = LoginForm()

    if not session.get('Login_attempts'):
        session['Login_attempts'] = 0

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data) .first()

        if not user or not user.verify_password(form.password.data) or not user.verify_pin(form.pin.data):
            session['Login_attempts'] += 1

            if session.get('Login_attempts') >= 3:
                flash(Markup('Number of incorrect login attempts exceeded. Please click <a href = "/reset" >here</a> to reset.'))
                return render_template('users/login.html')

            flash('Please check your login details and try again, '
                   '{} login attempts remaining'.format(3-session.get('Login_attempts')))
            return render_template('users/login.html', form=form)

        login_user(user)
        session['Login_attempts'] = 0
        if current_user.role == user:
            return redirect(url_for('lottery.lottery'))
        else:
            return redirect(url_for('admin.admin'))
    return render_template('users/login.html', form=form)


@users_blueprint.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session['Login_attempts'] = 0
    return redirect(url_for('index'))

@users_blueprint.route('/reset')
def reset():
    session['Login_attempts'] = 0
    return redirect(url_for('users.login'))

# view user account
@users_blueprint.route('/account')
@login_required
def account():
    return render_template('users/account.html',
                           acc_no=current_user.id,
                           email=current_user.email,
                           firstname=current_user.firstname,
                           lastname=current_user.lastname,
                           phone=current_user.phone)


@users_blueprint.route('/setup_2fa')
def setup_2fa():
    if 'email' not in session:
        ## redirects user to index/ home page
        return redirect(url_for('main.index'))
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        # if user does not exist redirect to index/ home page
        return redirect(url_for('main.index'))
        # if user does not exist remove email from app session
    del session['email']
    return render_template('users/setup_2fa.html', email=user.email, uri=user.get_2fa_uri()), 200, {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


@users_blueprint.route('/update_password', methods=['GET', 'POST'])
def update_password():
    form = PasswordForm()

    if form.validate_on_submit():

        if form.current_password.data != current_user.password:
            flash('Password must match current password')
        if form.new_password.data == current_user.password:
            flash('New password must not match current password')

        current_user.password = form.new_password.data
        db.session.commit()
        flash ('password change success')

        return redirect(url_for('users.account'))

    return render_template('users/update_password.html', form=form)
