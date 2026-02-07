from app.core import database
from app.models.user import User, user_favorites
from app.models.asset import Asset

print("Creating favorites table...")
# Create specifically the new table
user_favorites.create(database.engine, checkfirst=True)
print("Table created successfully!")
