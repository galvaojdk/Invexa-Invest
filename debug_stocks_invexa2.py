import sys
import os

# Ensure we are using invexa2 modules
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core import database
from app.models.asset import Asset
from app.models.user_target import UserTarget
from app.models.portfolio import Portfolio
from app.models.user import User
from app.models.dividend import DividendEvent
from app.services.valuation_service import valuation_service

# Use the ACTUAL database URL from the app if possible, or try to load from environment
# Assuming default SQLite for local dev usually:
SQLALCHEMY_DATABASE_URL = "sqlite:///c:/tanos/invexa/invexa2/sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_stocks():
    db = SessionLocal()
    print("--- DEBUGGING STOCKS (Invexa2) ---")
    
    # 1. Check Targets
    # We assume there is a logged in user, let's try to find the first one or a specific one if known
    # If uncertain, we list for all users or just the first active one.
    user = db.query(User).filter(User.is_active == True).first()
    if not user:
        print("No active user found.")
        return

    print(f"User: {user.email} (ID: {user.id})")
    
    targets = db.query(UserTarget).filter(UserTarget.user_id == user.id, UserTarget.target_type == 'category').all()
    print("Targets:")
    for t in targets:
        print(f"  - {t.name}: {t.target_percent}%")
        
    # Check if 'stock' is present
    stock_target = next((t for t in targets if t.name.lower() == 'stock'), None)
    if not stock_target:
        print("WARNING: No 'stock' category target defined!")
    
    # 2. Check Owned Stocks
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
    print("\nOwned Assets:")
    has_stock = False
    for item in portfolio:
        asset = item.asset
        if not asset: continue
        print(f"  - [{asset.type}] {asset.ticker}: Price={asset.price}, Qty={item.quantity}")
        if asset.type == 'stock':
            has_stock = True
            fp, status = valuation_service.calculate_fair_price(asset)
            print(f"    -> LPA={asset.lpa}, VPA={asset.vpa}, FairPrice={fp:.2f}, Status={status}")

    # 3. Check Top 'Stock' Candidates in DB (New Opportunities)
    print("\nTop 5 Stock Candidates (DB):")
    stocks = db.query(Asset).filter(Asset.type == 'stock', Asset.price > 0).order_by(Asset.liquidity_avg_2m.desc()).limit(5).all()
    
    if not stocks:
        print("No stocks found in database with price > 0.")
    
    for asset in stocks:
        fp, status = valuation_service.calculate_fair_price(asset)
        print(f"  - {asset.ticker}: Price={asset.price}, LPA={asset.lpa}, VPA={asset.vpa}, DY={asset.dy_12m}")
        print(f"    -> FairPrice={fp:.2f}, Status={status}")

if __name__ == "__main__":
    debug_stocks()
