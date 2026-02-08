from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class DividendEvent(Base):
    __tablename__ = "dividend_events"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    type = Column(String, nullable=False) # 'DIVIDEND', 'JCP', 'RENDIMENTO'
    amount = Column(Float, nullable=False)
    
    pay_date = Column(Date, nullable=False) # Data do Pagamento
    record_date = Column(Date, nullable=True) # Data Com
    
    asset = relationship("Asset", back_populates="dividends")
