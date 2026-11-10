from app.core import database
from app.models.asset import Asset
from sqlalchemy import text

db = database.SessionLocal()
# Check column existence first just in case
try:
    res = db.execute(text("SELECT ticker, shares_outstanding FROM assets WHERE ticker='WEGE3'")).fetchone()
    print(f"DB Result: {res}")
except Exception as e:
    print(f"Error: {e}")
db.close()
