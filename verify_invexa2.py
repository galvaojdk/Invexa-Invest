import sys
import os

# Ensure we are using invexa2 modules
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.user_target import UserTarget
from app.models.dividend import DividendEvent
from app.services.rebalance_service import rebalance_service

engine = create_engine('sqlite:///:memory:')
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

def verify_invexa2():
    db = SessionLocal()
    
    user = User(email="test2@test.com", hashed_password="pw", full_name="Tester2", is_active=True)
    db.add(user)
    db.commit()
    
    # 1. Setup Assets
    # EXPENSIVE STOCK (Should be filtered out)
    a1 = Asset(ticker="CARO3", type="stock", price=50.0, lpa=1.0, vpa=1.0, liquidity_avg_2m=1000000) 
    
    # CHEAP FII (Should be suggested)
    f1 = Asset(ticker="CHEAP11", type="fii", price=100.0, dy_12m=12.0, p_vp=0.9, liquidity_avg_2m=1000000)
    
    db.add_all([a1, f1])
    db.commit()
    
    # 2. Setup Targets (50/50)
    t1 = UserTarget(user_id=user.id, target_type='category', name='stock', target_percent=50.0)
    t2 = UserTarget(user_id=user.id, target_type='category', name='fii', target_percent=50.0)
    db.add_all([t1, t2])
    db.commit()
    
    # 3. Contribution
    contribution = 1000.0
    
    print(f"--- INVEXA 2 Verification ---")
    suggestions = rebalance_service.get_rebalance_suggestions(db, user.id, contribution)
    
    total_suggested = sum(s['suggested_amount'] for s in suggestions)
    print(f"Total Suggested: {total_suggested}")
    
    for s in suggestions:
        print(f"[{s['category']}] {s['ticker']}: {s['suggested_amount']} ({s['status']})")
        
    if total_suggested >= contribution * 0.9:
        print("\nSUCCESS: Logic working in Invexa2.")
    else:
        print("\nFAILURE: Logic NOT working in Invexa2.")

if __name__ == "__main__":
    verify_invexa2()
