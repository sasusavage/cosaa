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
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
class Setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text)

    @staticmethod
    def get(key, default=None):
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default
