from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import User, Portfolio, Candidate, Vote, Setting, Executive, Resource, Event, db
from functools import wraps
from werkzeug.utils import secure_filename
import csv
import io
import os

admin = Blueprint('admin', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def delete_upload(image_url):
    """Delete the physical file for a /uploads/<filename> URL. Safe to call with any URL."""
    if not image_url:
        return
    try:
        from urllib.parse import urlparse
        path = urlparse(image_url).path  # e.g. /uploads/hero_photo.jpg
        if path.startswith('/uploads/'):
            filename = os.path.basename(path)
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(full_path):
                os.remove(full_path)
    except Exception:
        pass  # Never crash a delete because of a missing file

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
        hero_image = request.form.get('hero_image')

        # Handle hero image upload
        if 'hero_image_file' in request.files:
            file = request.files['hero_image_file']
            if file and file.filename != '' and allowed_file(file.filename):
                delete_upload(Setting.get('hero_image'))  # remove old file
                filename = secure_filename(f"hero_{file.filename}")
                upload_path = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                hero_image = url_for('uploaded_file', filename=filename)
        
        # Update or create settings
        for key, value in [('hero_title', hero_title), ('hero_subtitle', hero_subtitle), ('hero_image', hero_image)]:
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
    current_image = Setting.get('hero_image', 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&h=600&fit=crop')
    return render_template('admin/edit_content.html', title=current_title, subtitle=current_subtitle, image=current_image)

# ── About page content ────────────────────────────────────────────────────────

@admin.route('/about', methods=['GET', 'POST'])
@admin_required
def edit_about():
    if request.method == 'POST':
        for key in ('about_mission', 'about_community', 'about_industry'):
            Setting.set(key, request.form.get(key, ''))
        db.session.commit()
        flash('About page updated.', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_about.html',
        about_mission=Setting.get('about_mission', ''),
        about_community=Setting.get('about_community', ''),
        about_industry=Setting.get('about_industry', ''))

# ── Executives ─────────────────────────────────────────────────────────────────

@admin.route('/executives')
@admin_required
def list_executives():
    execs = Executive.query.order_by(Executive.order).all()
    return render_template('admin/executives.html', executives=execs)

@admin.route('/executives/create', methods=['GET', 'POST'])
@admin_required
def create_executive():
    if request.method == 'POST':
        image_url = request.form.get('image_url', '')
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"exec_{file.filename}")
                upload_path = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                image_url = url_for('uploaded_file', filename=filename)
        exec_ = Executive(
            name=request.form.get('name'),
            role=request.form.get('role'),
            bio=request.form.get('bio'),
            image_url=image_url,
            linkedin_url=request.form.get('linkedin_url'),
            twitter_url=request.form.get('twitter_url'),
            order=int(request.form.get('order', 0))
        )
        db.session.add(exec_)
        db.session.commit()
        flash('Executive added.', 'success')
        return redirect(url_for('admin.list_executives'))
    return render_template('admin/create_executive.html')

@admin.route('/executives/<int:exec_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_executive(exec_id):
    exec_ = Executive.query.get_or_404(exec_id)
    if request.method == 'POST':
        exec_.name = request.form.get('name')
        exec_.role = request.form.get('role')
        exec_.bio = request.form.get('bio')
        exec_.linkedin_url = request.form.get('linkedin_url')
        exec_.twitter_url = request.form.get('twitter_url')
        exec_.order = int(request.form.get('order', 0))
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '' and allowed_file(file.filename):
                delete_upload(exec_.image_url)  # remove old file
                filename = secure_filename(f"exec_{file.filename}")
                upload_path = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                exec_.image_url = url_for('uploaded_file', filename=filename)
        elif request.form.get('image_url'):
            exec_.image_url = request.form.get('image_url')
        db.session.commit()
        flash('Executive updated.', 'success')
        return redirect(url_for('admin.list_executives'))
    return render_template('admin/create_executive.html', exec=exec_)

@admin.route('/executives/<int:exec_id>/delete', methods=['POST'])
@admin_required
def delete_executive(exec_id):
    exec_ = Executive.query.get_or_404(exec_id)
    delete_upload(exec_.image_url)
    db.session.delete(exec_)
    db.session.commit()
    flash('Executive removed.', 'success')
    return redirect(url_for('admin.list_executives'))

# ── Resources ──────────────────────────────────────────────────────────────────

@admin.route('/resources')
@admin_required
def list_resources():
    resources = Resource.query.order_by(Resource.order).all()
    return render_template('admin/resources.html', resources=resources)

@admin.route('/resources/create', methods=['GET', 'POST'])
@admin_required
def create_resource():
    if request.method == 'POST':
        res = Resource(
            title=request.form.get('title'),
            description=request.form.get('description'),
            link=request.form.get('link'),
            link_label=request.form.get('link_label', 'Explore'),
            icon_color=request.form.get('icon_color', 'blue'),
            order=int(request.form.get('order', 0))
        )
        db.session.add(res)
        db.session.commit()
        flash('Resource added.', 'success')
        return redirect(url_for('admin.list_resources'))
    return render_template('admin/create_resource.html')

@admin.route('/resources/<int:res_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_resource(res_id):
    res = Resource.query.get_or_404(res_id)
    if request.method == 'POST':
        res.title = request.form.get('title')
        res.description = request.form.get('description')
        res.link = request.form.get('link')
        res.link_label = request.form.get('link_label', 'Explore')
        res.icon_color = request.form.get('icon_color', 'blue')
        res.order = int(request.form.get('order', 0))
        db.session.commit()
        flash('Resource updated.', 'success')
        return redirect(url_for('admin.list_resources'))
    return render_template('admin/create_resource.html', resource=res)

@admin.route('/resources/<int:res_id>/delete', methods=['POST'])
@admin_required
def delete_resource(res_id):
    res = Resource.query.get_or_404(res_id)
    db.session.delete(res)
    db.session.commit()
    flash('Resource removed.', 'success')
    return redirect(url_for('admin.list_resources'))

# ── Events ─────────────────────────────────────────────────────────────────────

@admin.route('/events')
@admin_required
def list_events():
    events = Event.query.order_by(Event.order).all()
    return render_template('admin/events.html', events=events)

@admin.route('/events/create', methods=['GET', 'POST'])
@admin_required
def create_event():
    if request.method == 'POST':
        ev = Event(
            title=request.form.get('title'),
            date=request.form.get('date'),
            description=request.form.get('description'),
            order=int(request.form.get('order', 0))
        )
        db.session.add(ev)
        db.session.commit()
        flash('Event added.', 'success')
        return redirect(url_for('admin.list_events'))
    return render_template('admin/create_event.html')

@admin.route('/events/<int:ev_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_event(ev_id):
    ev = Event.query.get_or_404(ev_id)
    if request.method == 'POST':
        ev.title = request.form.get('title')
        ev.date = request.form.get('date')
        ev.description = request.form.get('description')
        ev.order = int(request.form.get('order', 0))
        db.session.commit()
        flash('Event updated.', 'success')
        return redirect(url_for('admin.list_events'))
    return render_template('admin/create_event.html', event=ev)

@admin.route('/events/<int:ev_id>/delete', methods=['POST'])
@admin_required
def delete_event(ev_id):
    ev = Event.query.get_or_404(ev_id)
    db.session.delete(ev)
    db.session.commit()
    flash('Event removed.', 'success')
    return redirect(url_for('admin.list_events'))

# ── Candidate management ───────────────────────────────────────────────────────

@admin.route('/candidates/<int:cand_id>/delete', methods=['POST'])
@admin_required
def delete_candidate(cand_id):
    candidate = Candidate.query.get_or_404(cand_id)
    delete_upload(candidate.image_url)
    db.session.delete(candidate)
    db.session.commit()
    flash('Candidate removed.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/portfolios/<int:port_id>/delete', methods=['POST'])
@admin_required
def delete_portfolio(port_id):
    portfolio = Portfolio.query.get_or_404(port_id)
    db.session.delete(portfolio)
    db.session.commit()
    flash('Portfolio removed.', 'success')
    return redirect(url_for('admin.dashboard'))

# ── Results ────────────────────────────────────────────────────────────────────

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
