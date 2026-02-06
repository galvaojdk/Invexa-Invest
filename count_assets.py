from app.core import database
from sqlalchemy import text

db = database.SessionLocal()
try:
    count_stock = db.execute(text("SELECT count(*) FROM assets WHERE type='stock'")).scalar()
    count_fii = db.execute(text("SELECT count(*) FROM assets WHERE type='fii'")).scalar()
    print(f"Stocks: {count_stock}")
    print(f"FIIs: {count_fii}")
except Exception as e:
    print(f"Error: {e}")
db.close()
