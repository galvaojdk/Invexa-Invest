from app.core.database import SessionLocal
from app.models.asset import Asset

db = SessionLocal()
try:
    assets = db.query(Asset).order_by(Asset.liquidity_avg_2m.desc()).limit(10).all()
    print(f"Top 10 Assets by Liquidity:")
    for a in assets:
        print(f"{a.ticker}: {a.liquidity_avg_2m}")
        
    # Check how many have > 1M
    count = db.query(Asset).filter(Asset.liquidity_avg_2m > 1000000).count()
    print(f"\nAssets with > 1M liquidity: {count}")
    
except Exception as e:
    print(e)
finally:
    db.close()
