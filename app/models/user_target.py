from sqlalchemy import Column, Integer, ForeignKey, Float, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserTarget(Base):
    __tablename__ = "user_targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Target can be for a specific category (e.g., 'stock', 'fii')
    # Or even a specific ticker (future proofing)
    target_type = Column(String)  # 'category' or 'asset'
    name = Column(String)         # 'stock', 'fii', or 'WEGE3'
    
    target_percent = Column(Float) # Percentage (e.g., 50.0)

    user = relationship("User", backref="targets")
