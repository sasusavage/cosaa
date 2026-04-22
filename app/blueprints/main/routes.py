from flask import Blueprint, render_template
from app.models import User, Portfolio, Setting, Executive, Resource, Event
from datetime import datetime, timezone

main = Blueprint('main', __name__)

def _s(key, default=''):
    return Setting.get(key, default)

def _voting_open():
    start_s = Setting.get('voting_start')
    end_s   = Setting.get('voting_end')
    if not start_s or not end_s:
        return False
    try:
        now = datetime.now(timezone.utc)
        s = datetime.fromisoformat(start_s)
        e = datetime.fromisoformat(end_s)
        if s.tzinfo is None: s = s.replace(tzinfo=timezone.utc)
        if e.tzinfo is None: e = e.replace(tzinfo=timezone.utc)
        return s <= now <= e
    except Exception:
        return False

@main.route('/')
def index():
    voting_open = _voting_open()
    total_users = User.query.count()
    voted_count = User.query.filter_by(has_voted=True).count()
    turnout = (voted_count / total_users * 100) if total_users > 0 else 0
    
    return render_template('main/index.html',
        voting_open=voting_open,
        turnout=turnout,
        voted_count=voted_count,
        total_users=total_users,
        portfolios=Portfolio.query.all() if voting_open else [],
        upcoming_events=Event.query.order_by(Event.order).all(),
        executives=Executive.query.order_by(Executive.order).limit(4).all(),
        hero_title=_s('hero_title', 'Empowering the Next Generation of African Innovators.'),
        hero_subtitle=_s('hero_subtitle', 'Welcome to CoSSA. Join our vibrant community of learners and leaders in tech.'),
        hero_image=_s('hero_image', 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&h=600&fit=crop'),
        home_execs_subtitle=_s('home_execs_subtitle', 'Meet the dedicated leaders of CoSSA 2025/2026 academic year.'),
        home_newsletter_title=_s('home_newsletter_title', 'Stay Informed, Join Now.'),
        home_newsletter_body=_s('home_newsletter_body', "Don't miss out on important announcements and upcoming CS workshops. Subscribe to the CoSSA Newsletter."),
    )

@main.route('/about')
def about():
    return render_template('main/about.html',
        about_mission=_s('about_mission', 'The Computer Science Students Association (CoSSA) aims to foster a collaborative environment where computing students can grow, innovate, and lead. We bridge the gap between classroom theory and industry practice through workshops, hackathons, and community building.'),
        about_community=_s('about_community', 'Join over 1,500 active members sharing knowledge and building the future of technology in Africa.'),
        about_industry=_s('about_industry', 'We partner with top tech firms to provide internships and mentorship opportunities for our members.'),
    )

@main.route('/executives')
def executives():
    return render_template('main/executives.html',
        executives=Executive.query.order_by(Executive.order).all())

@main.route('/resources')
def resources():
    return render_template('main/resources.html',
        resources=Resource.query.order_by(Resource.order).all())
