import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app.core import database
from app.models.user import User

def check_sub():
    db = next(database.get_db())
    # Find any premium user
    user = db.query(User).filter(User.is_premium == True).first()
    
    if not user:
        print("No premium user found.")
        return

    print(f"User: {user.email}")
    print(f"Subscription End Date: {user.subscription_end_date} (Type: {type(user.subscription_end_date)})")
    
    now = datetime.now()
    print(f"Current Time (datetime.now()): {now}")
    
    if user.subscription_end_date:
        delta = user.subscription_end_date - now
        print(f"Delta: {delta}")
        print(f"Delta Days: {delta.days}")
        print(f"Delta Seconds: {delta.seconds}")

if __name__ == "__main__":
    check_sub()
