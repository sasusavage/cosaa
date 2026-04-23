import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get('DATABASE_URL')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

with engine.connect() as conn:
    print("Executing Migration...")
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS share_sms_sent BOOLEAN DEFAULT FALSE"))
        conn.commit()
        print("✅ Column 'share_sms_sent' added successfully.")
    except Exception as e:
        print(f"❌ Error: {e}")
