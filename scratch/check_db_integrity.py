import os
import sys
from sqlalchemy import create_engine, inspect

# Add current directory to path to find app
sys.path.append(os.getcwd())

try:
    from app import create_app, db
    from app.models import Portfolio
    
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('portfolios')]
        
        if 'order' in columns:
            print("SUCCESS: 'order' column exists in 'portfolios' table.")
        else:
            print("MISSING: 'order' column is not in 'portfolios' table.")
            # Attempt to add it
            try:
                db.session.execute(db.text('ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS "order" INTEGER DEFAULT 0;'))
                db.session.commit()
                print("UPDATE: Successfully added 'order' column to 'portfolios' table.")
            except Exception as e:
                print(f"FAILURE: Could not add column: {e}")

except Exception as e:
    print(f"DATABASE ERROR: {e}")
