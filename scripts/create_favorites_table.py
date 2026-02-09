import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core import database
from app.models.user import User, user_favorites
from app.models.asset import Asset

print("Creating favorites table...")
# Create specifically the new table
user_favorites.create(database.engine, checkfirst=True)
print("Table created successfully!")
