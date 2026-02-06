from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core import database, security
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.api.routes.dashboard import get_current_active_user # Reutilizando auth logic temporariamente
from app.schemas import PortfolioItemCreate

router = APIRouter()

@router.get("/")
def read_portfolio(current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    items = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    
    # Enriquecer resposta
    result = []
    for item in items:
        asset = item.asset
        
        # Valuation Logic (Copied from assets.py for consistency)
        # Graham (Stocks)
        fair_price_graham = 0.0
        status = "Neutro"
        
        if asset.type == 'stock' and asset.lpa > 0 and asset.vpa > 0:
            try:
                fair_price = (22.5 * asset.lpa * asset.vpa) ** 0.5
                if asset.price < fair_price:
                    status = "Descontado"
                else:
                    status = "Caro"
            except:
                pass
        
        # Bazin (FIIs/Dividends)
        # Bazin = DY / 0.06
        if asset.dy_12m and asset.dy_12m > 0:
             dividend_val = (asset.price * (asset.dy_12m / 100))
             fair_price_bazin = dividend_val / 0.06
             
             if asset.type == 'fii':
                 if asset.price < fair_price_bazin:
                     status = "Descontado"
                 else:
                     status = "Neutro" 
             
             # Stock fallback
             elif status != "Descontado" and fair_price_bazin > asset.price:
                 status = "Bom Pagador"

        # Calcular rentabilidade simples
        current_val = item.quantity * item.asset.price
        cost_val = item.quantity * item.average_price
        diff = current_val - cost_val
        rent_pct = (diff / cost_val * 100) if cost_val > 0 else 0.0
        
        result.append({
            "ticker": item.asset.ticker,
            "quantity": item.quantity,
            "average_price": item.average_price,
            "current_price": item.asset.price,
            "total_value": current_val,
            "rentability_pct": round(rent_pct, 2),
            "rentability_val": diff,
            "recommendation": status
        })
    return result

from app.services import market_data

@router.post("/")
def add_to_portfolio(item: PortfolioItemCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    # Buscar ativo ou criar via Yahoo
    ticker_clean = item.ticker.upper().replace(".SA", "")
    
    # Usa o service para garantir que o ativo exista
    asset = market_data.get_or_create_asset(db, ticker_clean)
    
    if not asset:
        raise HTTPException(status_code=404, detail=f"Ativo '{ticker_clean}' não encontrado na B3/Yahoo Finance.")

    # Verificar se ja existe (somar posicao)
    portfolio_item = db.query(Portfolio).filter(Portfolio.user_id == current_user.id, Portfolio.asset_id == asset.id).first()
    
    if portfolio_item:
        # Recalcular PM (Media Ponderada)
        old_total = portfolio_item.quantity * portfolio_item.average_price
        new_total = item.quantity * item.average_price
        total_qty = portfolio_item.quantity + item.quantity
        
        portfolio_item.average_price = (old_total + new_total) / total_qty
        portfolio_item.quantity = total_qty
    else:
        portfolio_item = Portfolio(
            user_id=current_user.id,
            asset_id=asset.id,
            quantity=item.quantity,
            average_price=item.average_price
        )
        db.add(portfolio_item)
    
    db.commit()
    return {"message": "Ativo adicionado com sucesso"}

from app.services.transaction_service import TransactionService
from app.schemas import TransactionCreate

@router.post("/transaction")
def create_transaction(item: TransactionCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    try:
        TransactionService.process_transaction(
            db=db,
            user_id=current_user.id,
            ticker=item.ticker,
            type=item.type,
            quantity=item.quantity,
            price=item.price,
            date=item.date
        )
        return {"message": "Movimentação registrada com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


