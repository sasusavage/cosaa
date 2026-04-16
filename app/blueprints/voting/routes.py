from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Portfolio, Candidate, Vote, db
from functools import wraps

voting = Blueprint('voting', __name__)

@voting.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('voting.ballot'))
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        password = request.form.get('password')
        user = User.query.filter_by(student_id=student_id).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('voting.ballot'))
        flash('Invalid Student ID or password', 'error')
    return render_template('voting/login.html')

@voting.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@voting.route('/ballot')
@login_required
def ballot():
    if current_user.has_voted:
        return redirect(url_for('voting.already_voted'))
    portfolios = Portfolio.query.all()
    return render_template('voting/ballot.html', portfolios=portfolios)

@voting.route('/submit-vote', methods=['POST'])
@login_required
def submit_vote():
    # Double-check both the flag and the DB to prevent any race condition
    if current_user.has_voted:
        flash('You have already cast your ballot.', 'info')
        return redirect(url_for('voting.already_voted'))

    existing = Vote.query.filter_by(user_id=current_user.id).first()
    if existing:
        current_user.has_voted = True
        db.session.commit()
        return redirect(url_for('voting.already_voted'))

    portfolios = Portfolio.query.all()
    try:
        for portfolio in portfolios:
            selection = request.form.get(f'portfolio_{portfolio.id}')
            if selection:
                candidate_id = int(selection)
                vote = Vote(user_id=current_user.id, candidate_id=candidate_id, portfolio_id=portfolio.id)
                db.session.add(vote)

        current_user.has_voted = True
        db.session.commit()
        flash('Ballot submitted successfully! Your voice has been heard.', 'success')
        return redirect(url_for('voting.vote_confirmed'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during submission. Please try again.', 'error')
        print(f"Error submitting vote: {e}")
        return redirect(url_for('voting.ballot'))

@voting.route('/confirmed')
@login_required
def vote_confirmed():
    return render_template('voting/confirmed.html')

@voting.route('/already-voted')
@login_required
def already_voted():
    return render_template('voting/already_voted.html')
