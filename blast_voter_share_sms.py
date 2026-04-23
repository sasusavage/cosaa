import os
import sys
import time
from app import create_app, db
from app.models import User
from app.utils import send_sms

def run_blast():
    app = create_app()
    with app.app_context():
        print("\n" + "="*40)
        print("   CoSSA VOTER SHARE SMS BLAST V3")
        print("="*40 + "\n")
        
        # 1. Fetch all students who have voted AND have NOT received the share SMS
        # This prevents double-sending and saves credits.
        voters = User.query.filter_by(
            has_voted=True, 
            share_sms_sent=False, 
            role='student'
        ).all()
        
        if not voters:
            print("INFO: No new voters found who haven't received the SMS.")
            return

        phone_numbers_map = {v.id: v.phone_number for v in voters if v.phone_number}
        
        if not phone_numbers_map:
            print("INFO: No valid phone numbers found for the new voters.")
            return

        print(f"OK: Found {len(phone_numbers_map)} new voters.")

        # 2. Prepare the message
        site_url = os.environ.get('BASE_URL', 'https://cossa.sasulabs.me')
        message = (
            "CoSSA Elections 2026: I just voted! 🗳️ \n"
            "Help us reach 100% turnout. Share the link with your friends now: "
            f"{site_url}"
        )

        print("-" * 30)
        print(f"MESSAGE PREVIEW:\n{message}")
        print("-" * 30)

        confirm = input(f"\nProceed with sending to {len(phone_numbers_map)} people? (yes/no): ")
        if confirm.lower() != 'yes':
            print("ABORTED.")
            return

        # 3. Sending in batches and updating DB
        batch_size = 50 # Smaller batch to ensure we can update DB safely if it fails
        voter_ids = list(phone_numbers_map.keys())
        
        total_voters = len(voter_ids)
        for i in range(0, total_voters, batch_size):
            current_ids = voter_ids[i:i + batch_size]
            current_phones = [phone_numbers_map[vid] for vid in current_ids]
            
            print(f"Sending batch {i//batch_size + 1}...", end=" ", flush=True)
            
            result = send_sms(current_phones, message)
            
            if result:
                # MARK AS SENT IN DB
                User.query.filter(User.id.in_(current_ids)).update({User.share_sms_sent: True}, synchronize_session=False)
                db.session.commit()
                print("SUCCESS")
            else:
                print("FAILED (Skipping DB update for this batch)")
            
            if i + batch_size < total_voters:
                time.sleep(1)

        print("\nCampaign Finished!")

if __name__ == "__main__":
    run_blast()
