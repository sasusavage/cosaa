import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

def clear():
    app = Flask(__name__)
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("Explicitly dropping all tables...")
        # Use metadata directly to avoid model dependencies
        db.reflect()
        db.drop_all()
        print("Tables dropped. Re-running app to trigger create_all and seeding...")
    
    # Now that it's dropped, we can run the real app to recreate and seed defaults
    from app import create_app
    create_app()
    print("Database cleared and reset with default admin and settings.")

if __name__ == '__main__':
    clear()
