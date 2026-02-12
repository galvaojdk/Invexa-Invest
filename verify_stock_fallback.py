import sys
import os

# Ensure we are using invexa2 modules
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core import database
from app.models.user import User
from app.models.asset import Asset
from app.models.user_target import UserTarget
from app.services.valuation_service import valuation_service
from app.services.rebalance_service import rebalance_service

# Use in-memory DB for test
engine = create_engine('sqlite:///:memory:')
SessionLocal = sessionmaker(bind=engine)
# We need to import Base to create tables. 
# RebalanceService imports Portfolio, Asset, UserTarget.
# We also need User.
from app.core.database import Base # Hopefully all models are registered
# Ensure models are imported so Base knows them
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.user import User
from app.models.user_target import UserTarget
from app.models.dividend import DividendEvent

Base.metadata.create_all(bind=engine)

def verify_stock_fallback():
    db = SessionLocal()
    
    user = User(email="t3@t.com", hashed_password="pw", full_name="T3", is_active=True)
    db.add(user)
    db.commit()
    
    # Stock with MISSING fundamental data (LPA=0, VPA=0) so Graham fails.
    # But P/VP is 0.8 (Descontado).
    s1 = Asset(
        ticker="FALLBACK3", 
        type="stock", 
        price=80.0, 
        lpa=0.0, 
        vpa=0.0, 
        p_vp=0.8, 
        dy_12m=0.0,
        liquidity_avg_2m=5000000
    )
    
    db.add(s1)
    db.commit()
    
    # Target: 100% Stock
    t1 = UserTarget(user_id=user.id, target_type='category', name='stock', target_percent=100.0)
    db.add(t1)
    db.commit()
    
    # Valuation Check directly
    fp, status = valuation_service.calculate_fair_price(s1)
    print(f"Asset: {s1.ticker}, Price: {s1.price}, P/VP: {s1.p_vp}")
    print(f"Valuation Result: FairPrice={fp:.2f}, Status={status}")
    
    if status != "Descontado":
        print("FAILURE: Asset should be Descontado via P/VP fallback.")
        return

    # User Contribution
    contrib = 1000.0
    suggestions = rebalance_service.get_rebalance_suggestions(db, user.id, contrib)
    
    print("\nSuggestions:")
    for s in suggestions:
        print(f"- {s['ticker']}: {s['suggested_amount']} ({s['status']})")
        
    if any(s['ticker'] == 'FALLBACK3' for s in suggestions):
        print("\nSUCCESS: Stock fallback worked and asset was suggested.")
    else:
        print("\nFAILURE: Stock fallback asset NOT suggested.")

if __name__ == "__main__":
    verify_stock_fallback()
