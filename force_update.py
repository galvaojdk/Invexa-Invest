from app.core import database
from app.services import market_data

db = database.SessionLocal()
print("Updating all assets...")
market_data.update_all_assets(db)
print("Done.")

# Verify WEGE3 again
from sqlalchemy import text
res = db.execute(text("SELECT ticker, shares_outstanding FROM assets WHERE ticker='WEGE3'")).fetchone()
print(f"DB Result After Update: {res}")
db.close()
