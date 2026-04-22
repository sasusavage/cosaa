import os
import openpyxl
import sys

# Ensure we can import from app
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User

def inject():
    app = create_app()
    with app.app_context():
        file_path = "For Department.xlsx"
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found.")
            return
            
        print(f"Loading Master List: {file_path}...")
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        
        added = 0
        updated = 0
        
        print("Processing students...")
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0: continue # Skip header
            
            sid = str(row[0]).strip().upper() if row[0] else None
            surname = str(row[1]).strip() if row[1] else ""
            firstname = str(row[2]).strip() if row[2] else ""
            othernames = str(row[3]).strip() if row[3] else ""
            program = str(row[4]).strip() if row[4] else ""
            campus = str(row[5]).strip() if row[5] else ""
            dept = str(row[8]).strip() if row[8] else ""
            
            if not sid:
                continue
                
            # Construct display name
            full_name = f"{firstname} {othernames} {surname}".replace(" None", "").strip()
            if not full_name:
                full_name = sid
            
            user = User.query.filter_by(student_id=sid).first()
            if user:
                # Update existing record
                user.surname = surname
                user.firstname = firstname
                user.othernames = othernames
                user.program = program
                user.campus = campus
                user.department = dept
                user.username = full_name 
                updated += 1
            else:
                # Create new record
                new_user = User(
                    student_id=sid,
                    username=full_name,
                    surname=surname,
                    firstname=firstname,
                    othernames=othernames,
                    program=program,
                    campus=campus,
                    department=dept,
                    role='student'
                )
                db.session.add(new_user)
                added += 1
            
            if (added + updated) % 100 == 0:
                db.session.commit()
                print(f"Progress: {added + updated} records synced...")

        db.session.commit()
        print("\n" + "="*40)
        print("MASTER ONBOARDING COMPLETE")
        print(f"New Students Added: {added}")
        print(f"Students Updated:   {updated}")
        print("="*40)

if __name__ == "__main__":
    inject()
