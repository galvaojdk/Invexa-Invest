from app.core import database
from sqlalchemy import text

db = database.SessionLocal()
try:
    res = db.execute(text("SELECT ticker, net_income FROM assets WHERE ticker='WEGE3'")).fetchone()
    print(f"DB Result for WEGE3: {res}")
    
    res = db.execute(text("SELECT ticker, net_income FROM assets WHERE ticker='PETR4'")).fetchone()
    print(f"DB Result for PETR4: {res}")
except Exception as e:
    print(f"Error: {e}")
db.close()
