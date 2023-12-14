# IMPORTS
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm import make_transient

import models
from app import db, requires_roles
from lottery.forms import DrawForm
from models import Draw

# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')


# VIEWS
# view lottery page
@lottery_blueprint.route('/lottery')
@login_required
@requires_roles('user')
def lottery():
    # Render the lottery page for the authenticated user.
    return render_template('lottery/lottery.html', name=current_user.firstname)


# view all draws that have not been played
@lottery_blueprint.route('/create_draw', methods=['POST'])
@login_required
@requires_roles('user')
def create_draw():
    # form to handle submission of new lottery draw
    form = DrawForm()

    if form.validate_on_submit():
        # collect form data to create the draw
        submitted_numbers = (str(form.number1.data) + ' '
                          + str(form.number2.data) + ' '
                          + str(form.number3.data) + ' '
                          + str(form.number4.data) + ' '
                          + str(form.number5.data) + ' '
                          + str(form.number6.data))

        # Encrypt the submitted numbers using the user's post key
        encrypted_draw = models.encrypt(submitted_numbers, current_user.post_key)

        # create a new draw with the form data.
        new_draw = Draw(user_id= current_user.id, numbers=encrypted_draw, master_draw=False, lottery_round=0)

        # add the new draw to the database
        db.session.add(new_draw)
        db.session.commit()

        # re-render lottery.page
        flash('Draw %s submitted.' % submitted_numbers)
        return redirect(url_for('lottery.lottery'))

    return render_template('lottery/lottery.html', name=current_user.firstname, form=form)


# view all draws that have not been played
@lottery_blueprint.route('/view_draws', methods=['POST'])
@login_required
@requires_roles('user')
def view_draws():
    # get all draws that have not been played [played=0]
    playable_draws = Draw.query.filter_by(been_played=False, user_id=current_user.id).all()

    # if playable draws exist
    if len(playable_draws) != 0:
        # Decrypt the numbers for each playable draw
        for draw in playable_draws:
            make_transient(draw)
            draw.numbers = models.decrypt(draw.numbers, current_user.post_key)
        # re-render lottery page with playable draws

        return render_template('lottery/lottery.html', playable_draws=playable_draws)
    else:
        flash('No playable draws.')
        return lottery()


# check played draws and view lottery results
@lottery_blueprint.route('/check_draws', methods=['POST'])
@login_required
@requires_roles('user')
def check_draws():
    # get played draws
    played_draws = Draw.query.filter_by(been_played=True).all()

    # if played draws exist
    if len(played_draws) != 0:
        # Decrypt the numbers for each played draw
        for draw in played_draws:
            make_transient(draw)
            draw.numbers = models.decrypt(draw.numbers, current_user.post_key)
        # Render the lottery page with results
        return render_template('lottery/lottery.html', results=played_draws, played=True)

    # if no played draws exist all draw entries have been played therefore wait for next lottery round
    else:
        flash("Next round of lottery yet to play. Check you have playable draws.")
        return lottery()


# delete all played draws
@lottery_blueprint.route('/play_again', methods=['POST'])
@login_required
@requires_roles('user')
def play_again():
    # Delete all played draws (excluding master draws)
    Draw.query.filter_by(been_played=True, master_draw=False).delete(synchronize_session=False)
    db.session.commit()

    # Flash message and redirect to the lottery page
    flash("All played draws deleted.")
    return lottery()


