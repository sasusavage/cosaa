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
        print("   CoSSA VOTER SHARE SMS BLAST V2")
        print("="*40 + "\n")
        
        # 1. Fetch all students who have voted
        voters = User.query.filter_by(has_voted=True, role='student').all()
        
        if not voters:
            print("❌ No students found who have voted yet.")
            return

        phone_numbers = [v.phone_number for v in voters if v.phone_number]
        
        if not phone_numbers:
            print("❌ No valid phone numbers found for voters.")
            return

        print(f"✅ Found {len(phone_numbers)} voters.")

        # 2. Prepare the message
        # Short, punchy, and clear
        site_url = os.environ.get('BASE_URL', 'https://voting.cossa.org')
        message = (
            "CoSSA Elections 2026: I just voted! 🗳️ \n"
            "Help us reach 100% turnout. Share the link with your friends now: "
            f"{site_url}"
        )

        print("-" * 30)
        print(f"MESSAGE PREVIEW:\n{message}")
        print("-" * 30)

        confirm = input(f"\n🚀 Send this blast to {len(phone_numbers)} people? (yes/no): ")
        if confirm.lower() != 'yes':
            print("🛑 Aborted.")
            return

        # 3. Sending in batches of 100 as per best practices
        batch_size = 100
        total_batches = (len(phone_numbers) + batch_size - 1) // batch_size
        
        print(f"\n📦 Starting delivery in {total_batches} batches...")

        for i in range(0, len(phone_numbers), batch_size):
            batch = phone_numbers[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"Sending batch {batch_num}/{total_batches} ({len(batch)} numbers)...", end=" ", flush=True)
            
            result = send_sms(batch, message)
            
            if result:
                print("✅ Success")
            else:
                print("❌ FAILED")
            
            # Sublte delay to prevent API flooding
            if i + batch_size < len(phone_numbers):
                time.sleep(1)

        print("\n✨ SMS Blast Campaign Finished!")

if __name__ == "__main__":
    run_blast()
