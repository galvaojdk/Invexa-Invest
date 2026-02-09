
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core import database
from app.models.portfolio_history import PortfolioSnapshot

print("Creating portfolio history table...")
PortfolioSnapshot.__table__.create(database.engine, checkfirst=True)
print("Table 'portfolio_snapshots' created successfully!")
