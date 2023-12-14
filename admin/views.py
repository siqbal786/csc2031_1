# IMPORTS
import logging
import random
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user

from app import db, requires_roles
from models import User, Draw

# CONFIG
admin_blueprint = Blueprint('admin', __name__, template_folder='templates')


# VIEWS
# view admin homepage
@admin_blueprint.route('/admin')
# only logged in users can view function
@login_required
# logged in user must have role admin to access function
@requires_roles('admin')
def admin():
    # Check if the current user has the 'admin' role
    if current_user.role == 'admin':
        return render_template('admin/admin.html', name=current_user.firstname)
    else:
        # Redirect to the lottery page if the current user is not an admin
        return redirect(url_for('lottery.lottery'))


# create a new winning draw
@admin_blueprint.route('/generate_winning_draw')
@login_required
@requires_roles('admin')
def generate_winning_draw():

    # get current winning draw
    current_winning_draw = Draw.query.filter_by(master_draw=True).first()
    lottery_round = 1

    # if a current winning draw exists update lottery and delete existing draw
    if current_winning_draw:
        # update lottery round by 1
        lottery_round = current_winning_draw.lottery_round + 1
        db.session.delete(current_winning_draw)
        db.session.commit()

    # Generate new winning numbers for the draw
    winning_numbers = random.sample(range(1, 60), 6)
    winning_numbers.sort()
    winning_numbers_string = ''
    for i in range(6):
        winning_numbers_string += str(winning_numbers[i]) + ' '
    winning_numbers_string = winning_numbers_string[:-1]

    # create a new draw object.
    new_winning_draw = Draw(user_id=current_user.id, numbers=winning_numbers_string, master_draw=True, lottery_round=lottery_round)

    # add the new winning draw to the database
    db.session.add(new_winning_draw)
    db.session.commit()

    # flash message and re-render admin page
    flash("New winning draw %s added." % winning_numbers_string)
    return redirect(url_for('admin.admin'))


# view current winning draw
@admin_blueprint.route('/view_winning_draw')
@login_required
@requires_roles('admin')
def view_winning_draw():

    # get current unplayed winning draw from DB
    current_winning_draw = Draw.query.filter_by(master_draw=True,been_played=False).first()

    # If a winning draw exists, render admin page with the details
    if current_winning_draw:
        # re-render admin page with current winning draw and lottery round
        return render_template('admin/admin.html', winning_draw=current_winning_draw, name=current_user.firstname)

    # if no winning draw exists, rerender admin page
    flash("No valid winning draw exists. Please add new winning draw.")
    return redirect(url_for('admin.admin'))


# view lottery results and winners
@admin_blueprint.route('/run_lottery')
@login_required
@requires_roles('admin')
def run_lottery():

    # get current unplayed winning draw
    current_winning_draw = Draw.query.filter_by(master_draw=True, been_played=False).first()

    # if current unplayed winning draw exists
    if current_winning_draw:

        # get all unplayed user draws
        user_draws = Draw.query.filter_by(master_draw=False, been_played=False).all()
        results = []

        # if at least one unplayed user draw exists
        if user_draws:

            # update current winning draw as played
            current_winning_draw.been_played = True
            db.session.add(current_winning_draw)
            db.session.commit()

            # for each unplayed user draw
            for draw in user_draws:

                # get the owning user (instance/object)
                user = User.query.filter_by(id=draw.user_id).first()

                # if user draw matches current unplayed winning draw
                if draw.numbers == current_winning_draw.numbers:

                    # add details of winner to list of results
                    results.append((current_winning_draw.lottery_round, draw.numbers, draw.user_id, user.email))

                    # update draw as a winning draw (this will be used to highlight winning draws in the user's
                    # lottery page)
                    draw.matches_master = True

                # update draw as played
                draw.been_played = True

                # update draw with current lottery round
                draw.lottery_round = current_winning_draw.lottery_round

                # commit draw changes to DB
                db.session.add(draw)
                db.session.commit()

            # if no winners flash a message
            if len(results) == 0:
                flash("No winners.")

            # Render admin page with lottery results
            return render_template('admin/admin.html', results=results, name=current_user.firstname)

        # If no user draws entered, flash a message and redirect to admin page
        flash("No user draws entered.")
        return admin()

    # if current unplayed winning draw does not exist
    flash("Current winning draw expired. Add new winning draw for next round.")
    return redirect(url_for('admin.admin'))


# view all registered users
@admin_blueprint.route('/view_all_users')
@login_required
@requires_roles('admin')
def view_all_users():
    # Get all registered users with the 'user' role
    current_users = User.query.filter_by(role='user').all()

    # Render admin page with the list of users
    return render_template('admin/admin.html', name=current_user.firstname, current_users=current_users)


# view last 10 log entries
@admin_blueprint.route('/logs')
@login_required
@requires_roles('admin')
def logs():
    # Read the last 10 lines from the 'lottery.log' file
    with open("lottery.log", "r") as f:
        content = f.read().splitlines()[-10:]
        content.reverse()

    # Render admin page with log entries
    return render_template('admin/admin.html', logs=content, name=current_user.firstname)

# view user activity
@admin_blueprint.route('/view_user_activity')
@login_required
@requires_roles('admin')
def view_user_activity():
    # Get all registered users with the 'user' role
    current_users = User.query.filter_by(role='user').all()

    # Render admin page with user activity details
    return render_template('admin/admin.html', name=current_user.firstname, current_user_logs=current_users)