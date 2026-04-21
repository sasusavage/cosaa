from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    # student_id stored as UPPERCASE — lookup is case-insensitive
    student_id = db.Column(db.String(30), unique=True, index=True, nullable=False)
    username = db.Column(db.String(150))          # full display name
    hashed_password = db.Column(db.String(255))   # nullable — ID-only login students have no password
    surname = db.Column(db.String(100))
    firstname = db.Column(db.String(100))
    othernames = db.Column(db.String(100))
    program = db.Column(db.String(200))
    department = db.Column(db.String(200))
    campus = db.Column(db.String(100))
    phone_number = db.Column(db.String(20), index=True) # Index for lookups
    phone_verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(10))
    otp_expiry = db.Column(db.DateTime)
    has_voted = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(10), default='student')  # 'student' or 'admin'
    
    # 🕵️ Security & Hardware Locking
    last_ip = db.Column(db.String(45))
    current_session_id = db.Column(db.String(100))
    device_token = db.Column(db.String(100), index=True) # Persistent Hardware ID
    device_signature = db.Column(db.String(255))        # e.g. "Windows-Chrome-1920x1080"
    
    votes = db.relationship('Vote', backref='voter', lazy=True)

    @property
    def full_name(self):
        parts = [self.firstname or '', self.othernames or '', self.surname or '']
        return ' '.join(p for p in parts if p).strip() or self.student_id

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        if self.hashed_password:
            return check_password_hash(self.hashed_password, password)
        return False

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    candidates = db.relationship('Candidate', backref='portfolio', lazy=True, cascade="all, delete-orphan")
    votes = db.relationship('Vote', backref='portfolio', lazy=True)

class Candidate(db.Model):
    __tablename__ = 'candidates'
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    manifesto_summary = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    votes_received = db.relationship('Vote', backref='candidate', lazy=True)

class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # Supports IPv6
    user_agent = db.Column(db.String(255))
    
    # One vote per user per portfolio — enforced at DB level
    __table_args__ = (db.UniqueConstraint('user_id', 'portfolio_id', name='uq_user_portfolio_vote'),)

class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text)

    @staticmethod
    def get(key, default=None):
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            db.session.add(Setting(key=key, value=value))

class ElectionRecord(db.Model):
    """Immutable snapshot of a completed election — written once, never updated."""
    __tablename__ = 'election_records'
    id = db.Column(db.Integer, primary_key=True)
    academic_year = db.Column(db.String(20), nullable=False)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_students = db.Column(db.Integer, default=0)
    total_voted = db.Column(db.Integer, default=0)
    # Full results snapshot stored as JSON text
    results_json = db.Column(db.Text, nullable=False)

class Executive(db.Model):
    __tablename__ = 'executives'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    twitter_url = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)

class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    link = db.Column(db.String(255))
    link_label = db.Column(db.String(50), default='Explore')
    icon_color = db.Column(db.String(50), default='blue')
    order = db.Column(db.Integer, default=0)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
