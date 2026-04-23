import os
import sys
import time
from app import create_app, db
from app.models import User
from app.utils import send_sms

def run_results_blast():
    app = create_app()
    with app.app_context():
        print("\n" + "="*40)
        print("   CoSSA ELECTION RESULTS ANNOUNCEMENT")
        print("="*40 + "\n")
        
        # Fetch all students who have NOT received the results SMS
        students = User.query.filter_by(
            results_sms_sent=False, 
            role='student'
        ).all()
        
        if not students:
            print("INFO: All students have already been notified of the results.")
            return

        phone_numbers_map = {s.id: s.phone_number for s in students if s.phone_number}
        
        if not phone_numbers_map:
            print("INFO: No valid phone numbers found for the students.")
            return

        print(f"OK: Found {len(phone_numbers_map)} students to notify.")

        # Prepare the message
        site_url = os.environ.get('BASE_URL', 'https://cossa.sasulabs.me')
        message = (
            "CoSSA Election Results are OUT! \n"
            "The official certified winners have been announced. Visit the portal now to check the results: "
            f"{site_url}/results"
        )

        print("-" * 30)
        print(f"MESSAGE PREVIEW:\n{message}")
        print("-" * 30)

        confirm = input(f"\nProceed with sending to {len(phone_numbers_map)} people? (yes/no): ")
        if confirm.lower() != 'yes':
            print("ABORTED.")
            return

        # Sending in batches and updating DB
        batch_size = 50 
        student_ids = list(phone_numbers_map.keys())
        
        total_students = len(student_ids)
        for i in range(0, total_students, batch_size):
            current_ids = student_ids[i:i + batch_size]
            current_phones = [phone_numbers_map[sid] for sid in current_ids]
            
            print(f"Sending batch {i//batch_size + 1} ({len(current_phones)} recipients)...", end=" ", flush=True)
            
            result = send_sms(current_phones, message)
            
            if result:
                # MARK AS SENT IN DB
                User.query.filter(User.id.in_(current_ids)).update({User.results_sms_sent: True}, synchronize_session=False)
                db.session.commit()
                print("SUCCESS")
            else:
                print("FAILED (Skipping DB update for this batch)")
            
            if i + batch_size < total_students:
                time.sleep(1)

        print("\nResults Announcement Campaign Finished!")

if __name__ == "__main__":
    run_results_blast()
