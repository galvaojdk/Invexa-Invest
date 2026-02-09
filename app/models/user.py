from sqlalchemy import Boolean, Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association Table for Favorites
user_favorites = Table(
    "user_favorites",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("asset_id", Integer, ForeignKey("assets.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    role = Column(String, default="user")
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    
    # Subscription Fields
    subscription_end_date = Column(DateTime, nullable=True)
    subscription_status = Column(String, default="inactive") # inactive, active, expired, canceled
    subscription_plan = Column(String, default="free") # free, monthly, annual

    # Favorites
    favorites = relationship("Asset", secondary=user_favorites, backref="favorited_by")
