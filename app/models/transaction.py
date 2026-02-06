from sqlalchemy import Column, Integer, ForeignKey, Float, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))
    type = Column(String)  # 'BUY' or 'SELL'
    quantity = Column(Integer)
    price = Column(Float)
    total_value = Column(Float) # quantity * price
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # For Sales:
    profit_loss = Column(Float, default=0.0) # Realized P/L for this specific sale

    user = relationship("User", backref="transactions")
    asset = relationship("Asset")
