from app.core import database
from app.models.asset import Asset
from sqlalchemy.orm import Session

db = database.SessionLocal()
assets = db.query(Asset).filter(Asset.ticker.in_(['TAEE11', 'MXRF11', 'HGLG11'])).all()

for a in assets:
    print(f"Ticker: {a.ticker} | Type: {a.type} | Price: {a.price} | DY: {a.dy_12m} | LPA: {a.lpa} | VPA: {a.vpa} | NetIncome: {a.net_income}")

db.close()
