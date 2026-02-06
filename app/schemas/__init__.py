from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool = False
    is_premium: bool = False
    role: str = "user"
    class Config:
        from_attributes = True

class UserInDB(UserBase):
    hashed_password: str

# Asset Schemas
class AssetResponse(BaseModel):
    id: int
    ticker: str
    name: Optional[str] = ""
    sector: Optional[str] = ""
    type: str
    price: Optional[float] = 0.0
    dy_12m: Optional[float] = 0.0
    p_vp: Optional[float] = 0.0
    shares_outstanding: Optional[int] = 0
    net_income: Optional[float] = 0.0
    # Runtime fields
    fair_price_graham: Optional[float] = 0.0
    fair_price_bazin: Optional[float] = 0.0
    safe_margin: Optional[float] = 0.0
    status: Optional[str] = None

    class Config:
        from_attributes = True

class PortfolioItemCreate(BaseModel):
    ticker: str
    quantity: int
    average_price: float

class TransactionCreate(BaseModel):
    ticker: str
    type: str # BUY or SELL
    quantity: int
    price: float
    date: Optional[datetime] = None

class AlertBase(BaseModel):
    ticker: str
    type: str # price_above, price_below, dividend_announce
    target_price: Optional[float] = None

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    user_id: int
    is_active: bool
    triggered: bool
    created_at: Optional[datetime]
    class Config:
        from_attributes = True


