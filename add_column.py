from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    print("Adding 'share_sms_sent' column to 'users' table...")
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS share_sms_sent BOOLEAN DEFAULT FALSE"))
        db.session.commit()
        print("✅ Column added successfully.")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()
