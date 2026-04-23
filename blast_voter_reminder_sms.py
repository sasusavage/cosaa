import os
import sys
import time
from app import create_app, db
from app.models import User
from app.utils import send_sms

def run_reminder_blast():
    app = create_app()
    with app.app_context():
        print("\n" + "="*40)
        print("   CoSSA VOTER REMINDER SMS BLAST")
        print("="*40 + "\n")
        
        # 1. Fetch all students who have NOT voted AND have NOT received the reminder SMS
        voters = User.query.filter_by(
            has_voted=False, 
            reminder_sms_sent=False, 
            role='student'
        ).all()
        
        if not voters:
            print("INFO: No students found who haven't voted and haven't received the reminder.")
            return

        # Filter out users without phone numbers
        phone_numbers_map = {v.id: v.phone_number for v in voters if v.phone_number and len(v.phone_number) >= 10}
        
        if not phone_numbers_map:
            print("INFO: No valid phone numbers found for the target audience.")
            return

        print(f"OK: Found {len(phone_numbers_map)} students who haven't voted yet.")

        # 2. Prepare the message
        site_url = os.environ.get('BASE_URL', 'https://cossa.sasulabs.me')
        message = (
            "CoSSA Elections 2026: 🚨 Voting is ending soon! \n"
            "You haven't cast your vote yet. Make your voice heard now. \n"
            f"Vote here: {site_url}"
        )

        print("-" * 30)
        print(f"MESSAGE PREVIEW:\n{message}")
        print("-" * 30)

        confirm = input(f"\nProceed with sending reminder to {len(phone_numbers_map)} people? (yes/no): ")
        if confirm.lower() != 'yes':
            print("ABORTED.")
            return

        # 3. Sending in batches and updating DB
        batch_size = 50 
        voter_ids = list(phone_numbers_map.keys())
        
        total_voters = len(voter_ids)
        for i in range(0, total_voters, batch_size):
            current_ids = voter_ids[i:i + batch_size]
            current_phones = [phone_numbers_map[vid] for vid in current_ids]
            
            print(f"Sending batch {i//batch_size + 1} ({len(current_phones)} recipients)...", end=" ", flush=True)
            
            result = send_sms(current_phones, message)
            
            if result:
                # MARK AS SENT IN DB
                User.query.filter(User.id.in_(current_ids)).update({User.reminder_sms_sent: True}, synchronize_session=False)
                db.session.commit()
                print("SUCCESS")
            else:
                print("FAILED (Skipping DB update for this batch)")
            
            if i + batch_size < total_voters:
                time.sleep(1)

        print("\nReminder Campaign Finished!")

if __name__ == "__main__":
    run_reminder_blast()
