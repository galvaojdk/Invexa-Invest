import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.core import database
from app.services.market_data import fetch_batch_brapi
import asyncio

async def seed():
    db = database.SessionLocal()
    tickers = "PETR4,BBAS3,ITUB4,MXRF11,HGLG11"
    print(f"Seeding {tickers}...")
    await fetch_batch_brapi(db, tickers)
    db.close()

if __name__ == "__main__":
    asyncio.run(seed())
