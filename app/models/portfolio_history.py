from sqlalchemy import Column, Integer, Float, Date, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import date
from app.core.database import Base

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    snapshot_date = Column(Date, default=date.today, index=True)
    
    # Core Metrics
    total_equity = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    total_earnings = Column(Float, default=0.0) # Accum. Earnings Year or Total? Let's user proper context.
    rentability_pct = Column(Float, default=0.0)
    
    user = relationship("User", backref="snapshots")

    def __repr__(self):
        return f"<Snapshot user={self.user_id} date={self.snapshot_date} equity={self.total_equity}>"
