from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    print("Marking all current voters as 'share_sms_sent' to prevent double-blasting...")
    voters = User.query.filter_by(has_voted=True).all()
    count = 0
    for v in voters:
        v.share_sms_sent = True
        count += 1
    db.session.commit()
    print(f"Done. {count} voters marked as already sent.")
