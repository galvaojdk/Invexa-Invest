from sqlalchemy.orm import Session
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction
from app.models.asset import Asset
from datetime import datetime

class TransactionService:
    @staticmethod
    def process_transaction(db: Session, user_id: int, ticker: str, type: str, quantity: int, price: float, date: datetime = None, asset_type: str = None):
        # 1. Find Asset ID
        ticker = ticker.upper().replace(".SA", "")
        asset = db.query(Asset).filter(Asset.ticker == ticker).first()
        if not asset:
            # Try to fetch/create (auto-register)
            from app.services.market_data import get_or_create_asset
            asset = get_or_create_asset(db, ticker)
            if not asset:
                raise ValueError("Ativo não encontrado")
        
        # Override or set type if provided
        if asset_type:
            asset.type = asset_type.lower()
            db.commit()
            db.refresh(asset)

        asset_id = asset.id

        # 2. Get Portfolio Item
        portfolio_item = db.query(Portfolio).filter(
            Portfolio.user_id == user_id,
            Portfolio.asset_id == asset_id
        ).first()

        profit_loss = 0.0
        
        if not date:
            date = datetime.utcnow()

        if type == "BUY":
            # Logic: Update Average Price
            if not portfolio_item:
                portfolio_item = Portfolio(
                    user_id=user_id,
                    asset_id=asset_id,
                    quantity=quantity,
                    average_price=price
                )
                db.add(portfolio_item)
            else:
                total_cost_old = portfolio_item.quantity * portfolio_item.average_price
                total_cost_new = quantity * price
                new_qty = portfolio_item.quantity + quantity
                
                # PM = Total Cost / Total Qty
                portfolio_item.average_price = (total_cost_old + total_cost_new) / new_qty
                portfolio_item.quantity = new_qty
        
        elif type == "SELL":
            if not portfolio_item or portfolio_item.quantity < quantity:
                raise ValueError("Quantidade insuficiente para venda")
            
            # Logic: Realize Profit/Loss
            # PM does NOT change on Sell (FIFO logic usually implies same PM until position cleared, or weighted avg assumption)
            # P/L = (Sell Price - PM) * Qty
            profit_loss = (price - portfolio_item.average_price) * quantity
            
            portfolio_item.quantity -= quantity
            
            # If Qty is 0, keep item or delete? Usually keep with 0 to show history? 
            # Or transaction history is enough. Let's keep with 0 for now.
        
        # 3. Create Transaction Record
        transaction = Transaction(
            user_id=user_id,
            asset_id=asset_id,
            type=type,
            quantity=quantity,
            price=price,
            total_value=quantity * price,
            timestamp=date,
            profit_loss=profit_loss if type == "SELL" else 0.0
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
