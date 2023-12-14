# IMPORTS
import logging
from datetime import datetime

from flask import Blueprint, render_template, flash, redirect, url_for, session, request
from markupsafe import Markup

from app import db, app, logger
from models import User
from users.forms import RegisterForm, LoginForm, PasswordForm
from flask_login import login_user, logout_user, login_required, current_user

# CONFIG
users_blueprint = Blueprint('users', __name__, template_folder='templates')


# VIEWS

# View for user registration
@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # Create a signup form object
    form = RegisterForm()

    # If the request method is POST or the form is valid
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # If the email already exists in the database redirect with an error message
        if user:
            flash('Email address already exists')
            return render_template('users/register.html', form=form)

        logging.warning('SECURITY - User registration [%s, %s]', form.email.data, request.remote_addr)

        # Create a new user with the form data
        new_user = User(email=form.email.data,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        dob=form.dob.data,
                        postcode=form.postcode.data,
                        phone=form.phone.data,
                        password=form.password.data,
                        role='user')

        # Add the new user to database
        db.session.add(new_user)
        db.session.commit()

        session['email'] = new_user.email

        # Redirect to setup_2fa
        return redirect(url_for('users.setup_2fa'))

    # If the request method is GET or the form is not valid, re-render the signup page
    return render_template('users/register.html', form=form)


# View for user login
@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    # Initialize login attempts in session if not present
    if not session.get('Login_attempts'):
        session['Login_attempts'] = 0

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Invalid login attempt
        if not user or not user.verify_password(form.password.data) or not user.verify_pin(form.pin.data):
            logging.warning('SECURITY - Invalid Login [%s, %s]', form.email.data, request.remote_addr)
            session['Login_attempts'] += 1

            # If login attempts exceed 3, display a message and prevent further attempts
            if session.get('Login_attempts') >= 3:
                flash(Markup('Number of incorrect login attempts exceeded. Please click <a href="/reset">here</a> to reset.'))
                return render_template('users/login.html')

            flash('Please check your login details and try again, {} login attempts remaining'.format(3 - session.get('Login_attempts')))
            return render_template('users/login.html', form=form)

        login_user(user)

        logging.warning('SECURITY - Log in [%s, %s, %s]', current_user.id, current_user.email, request.remote_addr)

        session['Login_attempts'] = 0
        current_user.last_login = current_user.current_login
        current_user.current_login = datetime.now()
        db.session.commit()

        # Redirect based on user role
        if current_user.role == "admin":
            logging.warning('SECURITY - Unauthorised role based access [%s, %s, %s]', current_user.id, current_user.email, request.remote_addr)
            return redirect(url_for('admin.admin'))
        else:
            return redirect(url_for('lottery.lottery'))

    return render_template('users/login.html', form=form)


# View for user logout
@users_blueprint.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logging.warning('SECURITY - Log out [%s, %s, %s]', current_user.id, current_user.email, request.remote_addr)
    logout_user()

    session['Login_attempts'] = 0
    return redirect(url_for('index'))


# View to reset login attempts
@users_blueprint.route('/reset')
def reset():
    session['Login_attempts'] = 0
    return redirect(url_for('users.login'))


# View for user account information
@users_blueprint.route('/account')
@login_required
def account():
    return render_template('users/account.html', acc_no=current_user.id, email=current_user.email,
                           firstname=current_user.firstname, lastname=current_user.lastname, phone=current_user.phone)


# View for setting up Two-Factor Authentication
@users_blueprint.route('/setup_2fa')
def setup_2fa():
    if 'email' not in session:
        return redirect(url_for('main.index'))

    user = User.query.filter_by(email=session['email']).first()

    # Redirect if the user does not exist
    if not user:
        return redirect(url_for('main.index'))

    # Remove email from session if the user exists
    del session['email']
    return render_template('users/setup_2fa.html', email=user.email, uri=user.get_2fa_uri()), 200, {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


# View for updating the user's password
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
        flash('password change success')

        return redirect(url_for('users.account'))

    return render_template('users/update_password.html', form=form)
