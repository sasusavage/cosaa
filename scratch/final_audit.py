import os
import sys
sys.path.append(os.getcwd())
from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    count = User.query.filter_by(role='student').count()
    print(f"TOTAL STUDENTS IN DATABASE: {count}")
