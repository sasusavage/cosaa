from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import User, Portfolio, Candidate, Vote, Setting, db
from functools import wraps
from werkzeug.utils import secure_filename
import csv
import io
import os
import random
import string

admin = Blueprint('admin', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied!', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@admin_required
def root_redirect():
    return redirect(url_for('admin.dashboard'))

@admin.route('/dashboard')
@admin_required
def dashboard():
    total_users = User.query.count()
    voted_count = User.query.filter_by(has_voted=True).count()
    turnout = (voted_count / total_users * 100) if total_users > 0 else 0
    portfolios = Portfolio.query.all()
    return render_template('admin/dashboard.html', 
                          total_users=total_users, 
                          voted_count=voted_count, 
                          turnout=turnout,
                          portfolios=portfolios)

@admin.route('/candidates/create', methods=['GET', 'POST'])
@admin_required
def create_candidate():
    portfolios = Portfolio.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        summary = request.form.get('manifesto_summary')
        portfolio_id = request.form.get('portfolio_id')
        
        # Handle file upload
        image_url = request.form.get('image_url')
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"{portfolio_id}_{name.replace(' ', '_')}_{file.filename}")
                upload_path = current_app.config['UPLOAD_FOLDER']
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                file.save(os.path.join(upload_path, filename))
                # Store relative path for URL generation
                # We assume the upload folder is mounted/served correctly
                # If served from static/uploads:
                image_url = url_for('uploaded_file', filename=filename)

        if not image_url:
            image_url = 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400&h=400&fit=crop'
            
        candidate = Candidate(name=name, manifesto_summary=summary, portfolio_id=portfolio_id, image_url=image_url)
        db.session.add(candidate)
        db.session.commit()
        flash('Candidate added successfully.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_candidate.html', portfolios=portfolios)

@admin.route('/portfolios/create', methods=['GET', 'POST'])
@admin_required
def create_portfolio():
    if request.method == 'POST':
        title = request.form.get('title')
        if Portfolio.query.filter_by(title=title).first():
            flash('Portfolio already exists.', 'error')
            return redirect(url_for('admin.create_portfolio'))
        portfolio = Portfolio(title=title)
        db.session.add(portfolio)
        db.session.commit()
        flash('Portfolio created successfully.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/create_portfolio.html')

@admin.route('/credentials/upload', methods=['GET', 'POST'])
@admin_required
def upload_credentials():
    if request.method == 'POST':
        if 'student_csv' not in request.files:
            flash('No file uploaded.', 'error')
            return redirect(url_for('admin.upload_credentials'))
        
        file = request.files['student_csv']
        if file.filename == '':
            flash('Empty filename.', 'error')
            return redirect(url_for('admin.upload_credentials'))

        if file and file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.reader(stream)
            next(csv_input) # Skip header
            added = 0
            for row in csv_input:
                student_id = row[0]
                username = row[1]
                # Default temporary password to first part of student ID + 'cossa'
                temp_password = f"{student_id[:4]}cossa"
                if not User.query.filter_by(student_id=student_id).first():
                    new_user = User(student_id=student_id, username=username)
                    new_user.set_password(temp_password)
                    db.session.add(new_user)
                    added += 1
            db.session.commit()
            flash(f'Successfully imported {added} student credentials (temp pass: first4+cossa).', 'info')
            return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/upload_credentials.html')

@admin.route('/content', methods=['GET', 'POST'])
@admin_required
def edit_content():
    if request.method == 'POST':
        hero_title = request.form.get('hero_title')
        hero_subtitle = request.form.get('hero_subtitle')
        
        # Update or create settings
        for key, value in [('hero_title', hero_title), ('hero_subtitle', hero_subtitle)]:
            setting = Setting.query.filter_by(key=key).first()
            if not setting:
                setting = Setting(key=key, value=value)
                db.session.add(setting)
            else:
                setting.value = value
        
        db.session.commit()
        flash('Site content updated successfully.', 'success')
        return redirect(url_for('admin.dashboard'))
    
    current_title = Setting.get('hero_title', 'Empowering the Next Generation of African Innovators.')
    current_subtitle = Setting.get('hero_subtitle', 'Welcome to CoSSA. Join our vibrant community of learners and leaders in tech.')
    return render_template('admin/edit_content.html', title=current_title, subtitle=current_subtitle)

@admin.route('/results')
@admin_required
def results():
    data = []
    portfolios = Portfolio.query.all()
    for portfolio in portfolios:
        portfolio_results = []
        for candidate in portfolio.candidates:
            # Simple count of votes for this candidate
            count = Vote.query.filter_by(candidate_id=candidate.id).count()
            portfolio_results.append({
                'name': candidate.name,
                'count': count
            })
        data.append({
            'title': portfolio.title,
            'results': portfolio_results
        })
    return render_template('admin/results.html', data=data)
