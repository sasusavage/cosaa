import os
import openpyxl
import sys

# Ensure we can import from app
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User

def inject():
    # Load app with production config from .env
    app = create_app()
    with app.app_context():
        file_path = "LEVEL 100 DATABASE 25_26 (Responses).xlsx"
        if not os.path.exists(file_path):
            print("Error: Spreadsheet file not found in directory.")
            return
            
        print(f"Opening {file_path}...")
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        
        added = 0
        skipped = 0
        
        print("Starting injection loop...")
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0: continue # Ignore headers ('Timestamp', 'Enter your student ID', 'Enter your full name')
            
            sid = str(row[1]).strip().upper() if row[1] else None
            name = str(row[2]).strip() if row[2] else None
            
            if not sid or not name:
                continue
            
            # 🛡️ Safety Check: Avoid duplicates
            existing = User.query.filter_by(student_id=sid).first()
            if existing:
                skipped += 1
                continue
            
            # Create the student account
            new_student = User(
                student_id=sid,
                username=name,
                role='student'
            )
            db.session.add(new_student)
            added += 1
            
            # Batch commit to avoid overwhelming the DB
            if added % 50 == 0:
                db.session.commit()
                print(f"• Progress: {added} students injected...")

        db.session.commit()
        print("\n" + "="*40)
        print("🎉 INJECTION COMPLETE")
        print(f"✅ New Students Added: {added}")
        print(f"⏩ Records Skipped:    {skipped} (Already in database)")
        print("="*40)

if __name__ == "__main__":
    inject()
