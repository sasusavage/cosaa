from flask import Blueprint, render_template
from app.models import Candidate, Portfolio, Setting, Executive, Resource, Event

main = Blueprint('main', __name__)

@main.route('/')
def index():
    hero_title = Setting.get('hero_title', 'Empowering the Next Generation of African Innovators.')
    hero_subtitle = Setting.get('hero_subtitle', 'Welcome to CoSSA. Join our vibrant community of learners and leaders in tech.')
    hero_image = Setting.get('hero_image', 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&h=600&fit=crop')
    upcoming_events = Event.query.order_by(Event.order).all()
    executives = Executive.query.order_by(Executive.order).limit(4).all()
    return render_template('main/index.html',
                           portfolios=Portfolio.query.all(),
                           upcoming_events=upcoming_events,
                           executives=executives,
                           hero_title=hero_title,
                           hero_subtitle=hero_subtitle,
                           hero_image=hero_image)

@main.route('/about')
def about():
    about_mission = Setting.get('about_mission', 'The Computer Science Students Association (CoSSA) aims to foster a collaborative environment where computing students can grow, innovate, and lead. We bridge the gap between classroom theory and industry practice through workshops, hackathons, and community building.')
    about_community = Setting.get('about_community', 'Join over 1,500 active members sharing knowledge and building the future of technology in Africa.')
    about_industry = Setting.get('about_industry', 'We partner with top tech firms to provide internships and mentorship opportunities for our members.')
    return render_template('main/about.html',
                           about_mission=about_mission,
                           about_community=about_community,
                           about_industry=about_industry)

@main.route('/executives')
def executives():
    executives = Executive.query.order_by(Executive.order).all()
    return render_template('main/executives.html', executives=executives)

@main.route('/resources')
def resources():
    resources = Resource.query.order_by(Resource.order).all()
    return render_template('main/resources.html', resources=resources)
