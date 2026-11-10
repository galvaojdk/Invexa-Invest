from app.core import database
from app.models.asset import Asset
from sqlalchemy.orm import Session

db = database.SessionLocal()
targets = ['KNIP11', 'IRDM11', 'XPLG11', 'HGRU11']
assets = db.query(Asset).filter(Asset.ticker.in_(targets)).all()

for a in assets:
    print(f"Ticker: {a.ticker} | Price: {a.price} | P/VP (DB): {a.p_vp} | VPA (DB): {a.vpa}")

db.close()
