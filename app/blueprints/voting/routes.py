from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Portfolio, Vote, Setting, db

voting = Blueprint('voting', __name__)

def _voting_window():
    """Returns (is_open, start_str, end_str). start/end may be None."""
    from datetime import datetime, timezone
    start_s = Setting.get('voting_start')
    end_s   = Setting.get('voting_end')
    if not start_s or not end_s:
        return False, start_s, end_s
    try:
        now   = datetime.now(timezone.utc)
        start = datetime.fromisoformat(start_s)
        end   = datetime.fromisoformat(end_s)
        # Make timezone-aware if naive
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return start <= now <= end, start_s, end_s
    except Exception:
        return False, start_s, end_s

@voting.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('voting.ballot'))
    if request.method == 'POST':
        raw_id = (request.form.get('student_id') or '').strip().upper()
        # Try password login first (admin), then ID-only for students
        user = User.query.filter(
            db.func.upper(User.student_id) == raw_id
        ).first()
        password = request.form.get('password', '').strip()
        if user:
            # Admin always needs a password; students can log in with ID alone
            if user.role == 'admin' and not user.check_password(password):
                flash('Invalid credentials.', 'error')
                return render_template('voting/login.html', admin_mode=True)
            login_user(user)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('voting.ballot'))
        flash('Student ID not found. Please check and try again.', 'error')
    return render_template('voting/login.html')

@voting.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@voting.route('/ballot')
@login_required
def ballot():
    if current_user.role == 'admin':
        flash('Admins manage the system and cannot cast a vote.', 'info')
        return redirect(url_for('admin.dashboard'))
    if current_user.has_voted:
        return redirect(url_for('voting.already_voted'))
    is_open, _, _ = _voting_window()
    if not is_open:
        show_stats = Setting.get('live_stats_public', '0') == '1'
        return render_template('voting/voting_closed.html', show_stats=show_stats)
    portfolios = Portfolio.query.all()
    return render_template('voting/ballot.html', portfolios=portfolios)

@voting.route('/submit-vote', methods=['POST'])
@login_required
def submit_vote():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    is_open, _, _ = _voting_window()
    if not is_open:
        return redirect(url_for('voting.ballot'))
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
    show_stats = Setting.get('live_stats_public', '0') == '1'
    return render_template('voting/confirmed.html', show_stats=show_stats)

@voting.route('/already-voted')
@login_required
def already_voted():
    show_stats = Setting.get('live_stats_public', '0') == '1'
    return render_template('voting/already_voted.html', show_stats=show_stats)

@voting.route('/live-stats.json')
@login_required
def live_stats_json():
    voted_count = User.query.filter_by(has_voted=True).count()
    total_users = User.query.count()
    portfolios = Portfolio.query.all()
    data = []
    for p in portfolios:
        candidates = []
        for c in p.candidates:
            count = len(c.votes_received)
            pct = round(count / voted_count * 100, 1) if voted_count > 0 else 0
            candidates.append({'id': c.id, 'name': c.name, 'image_url': c.image_url or '', 'votes': count, 'pct': pct})
        data.append({'id': p.id, 'title': p.title, 'candidates': candidates})
    return jsonify(voted_count=voted_count, total_users=total_users,
                   turnout=round(voted_count / total_users * 100, 1) if total_users else 0,
                   portfolios=data)
