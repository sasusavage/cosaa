import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'voting.login'
migrate = Migrate()
csrf = CSRFProtect()

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
        # Add votes.user_id if the column doesn't exist yet (existing deployments).
        from sqlalchemy import text, inspect as sa_inspect
        insp = sa_inspect(db.engine)
        if 'votes' in insp.get_table_names():
            existing_cols = [c['name'] for c in insp.get_columns('votes')]
            if 'user_id' not in existing_cols:
                with db.engine.connect() as conn:
                    # Add nullable first so existing rows don't violate NOT NULL
                    conn.execute(text(
                        'ALTER TABLE votes ADD COLUMN user_id INTEGER REFERENCES users(id)'
                    ))
                    conn.commit()

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
