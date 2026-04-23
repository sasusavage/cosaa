import os
import sys
from app import create_app, db
from app.models import User
from app.utils import send_sms

def run_blast():
    app = create_app()
    with app.app_context():
        print("--- CoSSA Voter Share SMS Blast ---")
        
        # 1. Fetch all students who have voted
        voters = User.query.filter_by(has_voted=True, role='student').all()
        
        if not voters:
            print("No students found who have voted yet.")
            return

        phone_numbers = [v.phone_number for v in voters if v.phone_number]
        
        if not phone_numbers:
            print("No valid phone numbers found for voters.")
            return

        print(f"Found {len(phone_numbers)} voters.")

        # 2. Prepare the message
        # We use a short link (home page) and a catchy message
        site_url = os.environ.get('BASE_URL', 'https://voting.cossa.org') # Fallback if not set
        message = (
            "CoSSA Elections 2026: I just cast my vote! 🗳️ \n"
            "Help us reach 100% turnout. Share the link with your friends to vote now: "
            f"{site_url}"
        )

        print(f"Message: \n{message}\n")

        confirm = input(f"Send this blast to {len(phone_numbers)} people? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return

        # 3. Send SMS
        # Vynfy supports batching in the 'recipients' list
        result = send_sms(phone_numbers, message)
        
        if result:
            print(f"Successfully sent blast! Gateway ID: {result.get('id', 'N/A')}")
        else:
            print("Failed to send blast. Check Vynfy logs.")

if __name__ == "__main__":
    run_blast()
