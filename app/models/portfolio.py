from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))
    quantity = Column(Integer, default=0)
    average_price = Column(Float, default=0.0)

    user = relationship("User", backref="portfolio_items")
    asset = relationship("Asset")
