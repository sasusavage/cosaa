from flask import Blueprint, render_template
from app.models import Candidate, Portfolio, Setting

main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Dynamic home page content managed by admin
    hero_title = Setting.get('hero_title', 'Empowering the Next Generation of African Innovators.')
    hero_subtitle = Setting.get('hero_subtitle', 'Welcome to CoSSA. Join our vibrant community of learners and leaders in tech.')
    hero_image = Setting.get('hero_image', 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&h=600&fit=crop')
    
    # Fetch data for public portal
    portfolios = Portfolio.query.all()
    upcoming_events = [
        {'title': 'CoSSA Coding Challenge', 'date': 'April 15, 2026', 'description': 'Show off your skills!'},
        {'title': 'Tech Networking Night', 'date': 'May 2, 2026', 'description': 'Meet tech recruiters and alumni.'},
    ]
    return render_template('main/index.html', 
                          portfolios=portfolios, 
                          upcoming_events=upcoming_events,
                          hero_title=hero_title,
                          hero_subtitle=hero_subtitle)

@main.route('/about')
def about():
    return render_template('main/about.html')

@main.route('/executives')
def executives():
    # Display current executives (mock or database)
    return render_template('main/executives.html')

@main.route('/resources')
def resources():
    # Resources list for CS students
    return render_template('main/resources.html')
