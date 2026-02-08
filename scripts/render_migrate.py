
import sys
import os

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("Starting database migration for Render...")

try:
    from app.core.database import engine, Base
    
    # Import all models to ensure they are registered with Base
    from app.models.user import User, user_favorites
    from app.models.asset import Asset
    from app.models.transaction import Transaction
    from app.models.portfolio import Portfolio
    from app.models.portfolio_history import PortfolioSnapshot
    # Add other models here if needed in future

    print("Creating all missing tables...")
    Base.metadata.create_all(bind=engine)
    print("Database migration completed successfully!")

except Exception as e:
    print(f"Error during migration: {e}")
    sys.exit(1)
