import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'voting.login'
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Default configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-key-shhh')
    db_url = os.environ.get('DATABASE_URL', 'postgresql://username:password@localhost/cossa_db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    upload_folder = os.environ.get('UPLOAD_FOLDER') or os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    os.makedirs(upload_folder, exist_ok=True)

    if config_class:
        app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    # ── Error Handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500

    @app.errorhandler(429)
    def ratelimit_handler(e):
        from flask import render_template
        return render_template('errors/429.html'), 429

    # ── Session Pinning (Device Lock) ──────────────────────────────────────────
    @app.before_request
    def check_session_lock():
        from flask import session, redirect, url_for, flash, request
        from flask_login import current_user, logout_user
        
        # Only check for authenticated students (admins might need multi-session)
        if current_user.is_authenticated and current_user.role == 'student':
            # 1. Check Session SID (Prevent concurrent devices)
            stored_sid = current_user.current_session_id
            active_sid = session.get('sid')
            
            if stored_sid and active_sid != stored_sid:
                logout_user()
                flash('Your account was logged in on another device. Please log in again for security.', 'info')
                return redirect(url_for('voting.login'))
            
            # 2. Check IP (Strict binding)
            if current_user.last_ip and request.remote_addr != current_user.last_ip:
                logout_user()
                flash('Your session location has changed. For security, please log in again.', 'warning')
                return redirect(url_for('voting.login'))

    # Register Blueprints
    from .blueprints.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .blueprints.voting.routes import voting as voting_blueprint
    app.register_blueprint(voting_blueprint, url_prefix='/vote')

    from .blueprints.admin.routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .models import User

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.context_processor
    def inject_site_settings():
        from .models import Setting
        return {
            'site_footer_description': Setting.get('footer_description', 'The Computer Science Students Association is dedicated to building the future of African tech leaders through community and innovation.'),
            'site_footer_email':       Setting.get('footer_email', 'info@cossa.com'),
            'site_footer_address':     Setting.get('footer_address', 'CS Dept block, VVU'),
            'site_footer_copyright':   Setting.get('footer_copyright', '2026 CoSSA. Designed for Excellence.'),
        }

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .models import User
    with app.app_context():
        db.create_all()

        # ── Schema migrations (idempotent) ────────────────────────────────────
        from sqlalchemy import text, inspect as sa_inspect
        insp = sa_inspect(db.engine)

        # votes.user_id
        if 'votes' in insp.get_table_names():
            vote_cols = [c['name'] for c in insp.get_columns('votes')]
            with db.engine.connect() as conn:
                if 'user_id' not in vote_cols:
                    conn.execute(text('ALTER TABLE votes ADD COLUMN user_id INTEGER REFERENCES users(id)'))
                if 'ip_address' not in vote_cols:
                    conn.execute(text('ALTER TABLE votes ADD COLUMN ip_address VARCHAR(45)'))
                if 'user_agent' not in vote_cols:
                    conn.execute(text('ALTER TABLE votes ADD COLUMN user_agent VARCHAR(255)'))
                conn.commit()

        # New User columns (added when we extended the model)
        if 'users' in insp.get_table_names():
            user_cols = [c['name'] for c in insp.get_columns('users')]
            new_user_cols = {
                'surname':    'VARCHAR(100)',
                'firstname':  'VARCHAR(100)',
                'othernames': 'VARCHAR(100)',
                'program':    'VARCHAR(200)',
                'department': 'VARCHAR(200)',
                'campus':     'VARCHAR(100)',
                'phone_number': 'VARCHAR(20)',
                'phone_verified': 'BOOLEAN DEFAULT FALSE',
                'phone_verified': 'BOOLEAN DEFAULT FALSE', # Safety
                'otp':         'VARCHAR(10)',
                'otp_expiry':  'TIMESTAMP',
                'last_ip':     'VARCHAR(45)',
                'current_session_id': 'VARCHAR(100)',
            }
            with db.engine.connect() as conn:
                for col, col_type in new_user_cols.items():
                    if col not in user_cols:
                        conn.execute(text(f'ALTER TABLE users ADD COLUMN {col} {col_type}'))
                conn.commit()

        # ── election_records table (new) — created by db.create_all above ────
        # No manual ALTER needed; SQLAlchemy creates it fresh if missing.

        # ── Seed default Settings ─────────────────────────────────────────────
        from .models import Setting
        _defaults = {
            'hero_title':            'Empowering the Next Generation of African Innovators.',
            'hero_subtitle':         'Welcome to CoSSA. Join our vibrant community of learners and leaders in tech.',
            'hero_image':            'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&h=600&fit=crop',
            'home_execs_subtitle':   'Meet the dedicated leaders of CoSSA 2025/2026 academic year.',
            'home_newsletter_title': 'Stay Informed, Join Now.',
            'home_newsletter_body':  "Don't miss out on important announcements and upcoming CS workshops. Subscribe to the CoSSA Newsletter.",
            'about_mission':         'The Computer Science Students Association (CoSSA) aims to foster a collaborative environment where computing students can grow, innovate, and lead. We bridge the gap between classroom theory and industry practice through workshops, hackathons, and community building.',
            'about_community':       'Join over 1,500 active members sharing knowledge and building the future of technology in Africa.',
            'about_industry':        'We partner with top tech firms to provide internships and mentorship opportunities for our members.',
            'footer_description':    'The Computer Science Students Association is dedicated to building the future of African tech leaders through community and innovation.',
            'footer_email':          'info@cossa.com',
            'footer_address':        'CS Dept block, VVU',
            'footer_copyright':      '2026 CoSSA. Designed for Excellence.',
            'live_stats_public':     '0',
            'stats_display_hours':   '48',
            'academic_year':         '',
        }
        for key, value in _defaults.items():
            if Setting.query.filter_by(key=key).first() is None:
                db.session.add(Setting(key=key, value=value))
        db.session.commit()

        # ── Seed default admin ────────────────────────────────────────────────
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', student_id='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        elif admin.role != 'admin':
            admin.role = 'admin'
            db.session.commit()

    return app
