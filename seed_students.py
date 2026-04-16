"""
Seed students from the department Excel file into the database.

Usage (run from the project root):
    python seed_students.py

Reads: For Department.xlsx  (must be in the project root)
Inserts only new records — existing student IDs are skipped.
"""
import os, openpyxl
from app import create_app, db
from app.models import User

EXCEL_PATH = os.path.join(os.path.dirname(__file__), 'For Department.xlsx')

def seed():
    app = create_app()
    with app.app_context():
        wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
        ws = wb.active

        added = skipped = 0
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:          # header row
                print('Columns:', row)
                continue
            if not row[0]:
                continue

            sid        = str(row[0]).strip().upper()
            surname    = str(row[1]).strip() if row[1] else ''
            firstname  = str(row[2]).strip() if row[2] else ''
            othernames = str(row[3]).strip() if row[3] else ''
            program    = str(row[4]).strip() if row[4] else ''
            campus     = str(row[5]).strip() if row[5] else ''
            department = str(row[8]).strip() if len(row) > 8 and row[8] else ''
            full_name  = ' '.join(p for p in [firstname, othernames, surname] if p)

            exists = User.query.filter(
                db.func.upper(User.student_id) == sid
            ).first()
            if exists:
                skipped += 1
                continue

            u = User(
                student_id=sid,
                username=full_name,
                surname=surname,
                firstname=firstname,
                othernames=othernames,
                program=program,
                campus=campus,
                department=department,
                role='student',
            )
            db.session.add(u)
            added += 1

        db.session.commit()
        print(f'\nDone. {added} students added, {skipped} already existed.')

if __name__ == '__main__':
    seed()
