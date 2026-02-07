from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)  # Ex: WEGE3, HGLG11
    name = Column(String, nullable=True)
    type = Column(String, nullable=False)  # 'stock' or 'fii'
    sector = Column(String, nullable=True)
    
    # Financial Data
    price = Column(Float, nullable=True)
    dy_12m = Column(Float, default=0.0)  # Dividend Yield 12m (%)
    p_vp = Column(Float, default=0.0)    # Preço / Valor Patrimonial
    lpa = Column(Float, default=0.0)     # Lucro por Ação
    vpa = Column(Float, default=0.0)     # Valor Patrimonial por Ação
    liquidity_avg_2m = Column(Float, default=0.0) # Liquidez média diária
    vacancy = Column(Float, default=0.0) # Vacância (apenas FIIs)
    num_properties = Column(Integer, default=0) # Qtd Imóveis (FIIs)
    shares_outstanding = Column(BigInteger, default=0) # Numero de papeis
    net_income = Column(Float, default=0.0) # Lucro Liquido (12m)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())
