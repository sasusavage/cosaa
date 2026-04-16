from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    hashed_password = db.Column(db.String(255))
    student_id = db.Column(db.String(20), unique=True, index=True)
    has_voted = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(10), default='student') # 'student' or 'admin'
    votes = db.relationship('Vote', backref='voter', lazy=True)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

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
