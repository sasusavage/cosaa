from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Portfolio, Vote, Setting, db
from app.utils import send_sms, generate_otp
from datetime import datetime, timedelta, timezone

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
        # Try password login first (admin)
        user = User.query.filter(
            db.func.upper(User.student_id) == raw_id
        ).first()
        
        password = request.form.get('password', '').strip()
        
        if user:
            # ── ADMIN LOGIC (Password) ────────────────────────────────────────
            if user.role == 'admin':
                if user.check_password(password):
                    login_user(user)
                    return redirect(url_for('admin.dashboard'))
                else:
                    flash('Invalid admin credentials.', 'error')
                    return render_template('voting/login.html', admin_mode=True)
            
            # ── STUDENT LOGIC (SMS OTP) ───────────────────────────────────────
            if not user.phone_number:
                # Phone missing - send to registration step
                return render_template('voting/provide_phone.html', user=user)
            
            # Phone exists - generate and send OTP
            otp = generate_otp()
            user.otp = otp
            user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
            db.session.commit()
            
            # Send SMS
            message = f"Your CoSSA Voting Verification Code is: {otp}. This code expires in 10 minutes."
            sms_sent = send_sms(user.phone_number, message)
            
            if sms_sent:
                return render_template('voting/verify_otp.html', student_id=user.student_id)
            else:
                flash('OTP generated but failed to send SMS. Please try again.', 'error')
                return redirect(url_for('voting.login'))
                
        flash('Student ID not found. Please check and try again.', 'error')
    return render_template('voting/login.html')

@voting.route('/verify-otp', methods=['POST'])
def verify_otp():
    student_id = request.form.get('student_id')
    otp_input = request.form.get('otp')
    
    user = User.query.filter(
        db.func.upper(User.student_id) == student_id.upper()
    ).first()
    
    if user and user.otp == otp_input:
        # Check expiry
        if user.otp_expiry and user.otp_expiry > datetime.now(timezone.utc):
            # Clear OTP and login
            user.otp = None
            user.otp_expiry = None
            db.session.commit()
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('voting.ballot'))
        else:
            flash('Your verification code has expired. Please request a new one.', 'error')
    else:
        flash('Invalid verification code. Please try again.', 'error')
        
    return render_template('voting/verify_otp.html', student_id=student_id)

@voting.route('/register-phone', methods=['POST'])
def register_phone():
    student_id = request.form.get('student_id')
    phone = request.form.get('phone_number').strip()
    
    if not phone:
        flash('Phone number is required.', 'error')
        return redirect(url_for('voting.login'))
        
    user = User.query.filter(
        db.func.upper(User.student_id) == student_id.upper()
    ).first()
    
    if user:
        # Save phone number
        user.phone_number = phone
        
        # Generate and send OTP immediately
        otp = generate_otp()
        user.otp = otp
        user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.session.commit()
        
        message = f"Your CoSSA Voting Verification Code is: {otp}. This code expires in 10 minutes."
        if send_sms(user.phone_number, message):
            return render_template('voting/verify_otp.html', student_id=user.student_id)
        else:
            flash('Phone saved but failed to send verification SMS. Please try again.', 'error')
            
    return redirect(url_for('voting.login'))

@voting.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

def _should_show_stats():
    """Show live stats if admin toggled on AND (voting still open OR within display-hours window after close)."""
    if Setting.get('live_stats_public', '0') != '1':
        return False
    from datetime import datetime, timezone
    end_s = Setting.get('voting_end')
    if not end_s:
        return True  # no end set — always show when toggled on
    try:
        end = datetime.fromisoformat(end_s)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now <= end:
            return True  # voting still open
        hours = float(Setting.get('stats_display_hours', '48') or '48')
        from datetime import timedelta
        return now <= end + timedelta(hours=hours)
    except Exception:
        return True

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
        show_stats = _should_show_stats()
        academic_year = Setting.get('academic_year', '')
        return render_template('voting/voting_closed.html', show_stats=show_stats, academic_year=academic_year)
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
    show_stats = _should_show_stats()
    academic_year = Setting.get('academic_year', '')
    return render_template('voting/confirmed.html', show_stats=show_stats, academic_year=academic_year)

@voting.route('/already-voted')
@login_required
def already_voted():
    show_stats = _should_show_stats()
    academic_year = Setting.get('academic_year', '')
    return render_template('voting/already_voted.html', show_stats=show_stats, academic_year=academic_year)

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
