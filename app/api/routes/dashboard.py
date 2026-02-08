from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from app.core import database, security
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.dividend import DividendEvent
from datetime import date, timedelta
from app.api.routes.auth import get_user_by_email # Helper temporário ou mover auth dependencies

router = APIRouter()

def get_current_user(token: str = Depends(security.settings.API_V1_STR), db: Session = Depends(database.get_db)):
    # Em uma implementação real completa, usaríamos o OAuth2PasswordBearer
    # Mas aqui vamos simplificar assumindo que o endpoint valida o token via header manualmente ou middleware
    # como placeholder para MVP
    pass

# Dependência de User simplificada para MVP (usando um mock de 'current user' baseado num token dummy ou esperar header)
# Para fazer direito agora, vamos implementar o get_current_user real baseado no auth.py

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

from fastapi import HTTPException, status
from jose import JWTError, ExpiredSignatureError

async def get_current_active_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.jwt.decode(token, security.settings.SECRET_KEY, algorithms=[security.settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

@router.get("/summary")
def get_dashboard_summary(current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    # Buscar Portfolio do usuario
    portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    
    total_equity = 0.0
    total_cost = 0.0
    total_earnings_12m = 0.0 
    asset_count = len(portfolio_items)
    
    type_allocation = {}
    assets_list = []
    
    for item in portfolio_items:
        asset = item.asset
        
        # Safety check: if asset was deleted but portfolio item remains
        if not asset:
            continue
        
        # Valores
        current_val = item.quantity * (asset.price or 0.0) # Handle None price
        cost_val = item.quantity * item.average_price
        
        total_equity += current_val
        total_cost += cost_val
        
        # Lucro/Prejuizo Item
        profit = current_val - cost_val
        profit_pct = (profit / cost_val * 100) if cost_val > 0 else 0.0
        
        # Proventos (Estimativa 12m baseada no DY)
        # DY é anual. Valor bruto anual = Valor investido (ou atual?) * DY.
        # Geralmente DY é sobre preço atual.
        yearly_earnings = current_val * ((asset.dy_12m or 0.0) / 100)
        total_earnings_12m += yearly_earnings
        
        # Alocação por Tipo
        asset_type = asset.type or "Outros"
        # Normalizar label
        type_label = "Ações" if asset_type == "stock" else "FIIs" if asset_type == "fii" else asset_type.title()
        type_allocation[type_label] = type_allocation.get(type_label, 0) + current_val
        
        # Dados para Tabela
        item_data = {
            "ticker": asset.ticker,
            "quantity": item.quantity,
            "average_price": item.average_price,
            "current_price": asset.price or 0.0,
            "total_value": current_val,
            "profit_val": profit,
            "profit_pct": profit_pct,
            "wallet_pct": 0, # Calc after total
            "recommendation": "Neutro", # Placeholder
            "magic_number": 0,
            "magic_number_progress": 0,
            "magic_number_remain": 0,
            "badges": []
        }

        # --- Magic Number (Bola de Neve) ---
        # Formula: Need (Price / Monthly Dividends) shares to buy 1 new share.
        # Monthly Dividends = Price * (DY / 12)
        # So: Target = Price / (Price * DY/12) = 1 / (DY/12) = 12 / DY
        # DY must be decimal.
        # asset.dy_12m is percentage (e.g. 12.5).
        
        dy_val = asset.dy_12m or 0.0
        if dy_val > 0:
            dy_decimal = dy_val / 100.0
            # Target Shares to buy 1 share/month with dividends
            target_shares = 12 / dy_decimal
            
            # Progress
            owned = item.quantity
            progress = (owned / target_shares) * 100 if target_shares > 0 else 0
            remain = max(0, int(target_shares - owned))
            
            item_data["magic_number"] = int(target_shares)
            item_data["magic_number_progress"] = min(100, progress)
            item_data["magic_number_remain"] = remain
            
        # --- Badges Logic ---
        badges = []
        
        # 1. P/VP Opportunity (FIIs only)
        if asset.type == 'fii' and asset.p_vp and asset.p_vp > 0:
            if asset.p_vp < 0.90:
                badges.append({"label": "Desconto", "color": "emerald", "full": f"P/VP {asset.p_vp:.2f}"})
            elif asset.p_vp > 1.20:
                badges.append({"label": "Caro?", "color": "red", "full": f"P/VP {asset.p_vp:.2f}"})
        
        # 2. Dividend Payer
        if dy_val > 14.0:
             badges.append({"label": "Dividend King", "color": "orange", "full": f"DY {dy_val:.1f}%"})
        elif dy_val > 8.0:
             badges.append({"label": "Pagador", "color": "blue", "full": f"DY {dy_val:.1f}%"})
            
        # 3. Valuation (Simplistic P/L for Stocks)
        if asset.type == 'stock' and asset.price and asset.lpa and asset.lpa > 0:
            p_l = asset.price / asset.lpa
            if p_l < 5.0:
                badges.append({"label": "Barato", "color": "emerald", "full": f"P/L {p_l:.1f}"})
        
        item_data["badges"] = badges
        assets_list.append(item_data)


    # --- Totals Calculation ---
    total_profit_val = total_equity - total_cost
    total_profit_pct = (total_profit_val / total_cost * 100) if total_cost > 0 else 0.0

    # --- Chart Data Preparation ---
    # Sort allocation for nice chart
    sorted_alloc = sorted(type_allocation.items(), key=lambda x: x[1], reverse=True)
    chart_labels = [k for k, v in sorted_alloc]
    chart_values = [v for k, v in sorted_alloc]

    # --- Recommendations Feature REMOVED at User Request (Legal compliance) ---
    recommendations = []
    visible_recs = []
    hidden_count = 0

    # Subscription Status
    sub_status = {
        "is_premium": current_user.is_premium,
        "plan": current_user.subscription_plan,
        "status": current_user.subscription_status,
        "days_remaining": 0,
        "end_date": None
    }
    
    if current_user.is_premium and current_user.subscription_end_date:
        from datetime import datetime
        now = datetime.now()
        delta = current_user.subscription_end_date - now
        
        # If delta.days is 0 but it's positive (e.g. 23 hours left), we should show 1 day or < 1 day.
        # But commonly 'days' property of timedelta just gives full days.
        # If it's less than 24h, delta.days is 0.
        
        # Adjust logic: if end_date > now, at least 1 day or "Expires Today"
        # However, user likely wants to see "30 days" right after purchase.
        
        # Calculate total seconds and convert to days rounding up
        total_seconds = delta.total_seconds()
        if total_seconds > 0:
             import math
             days_remaining = math.ceil(total_seconds / 86400)
             sub_status["days_remaining"] = days_remaining
        else:
             sub_status["days_remaining"] = 0
             
        sub_status["end_date"] = current_user.subscription_end_date.strftime("%d/%m/%Y")

    # --- History Snapshot Logic ---
    from datetime import date
    from app.models.portfolio_history import PortfolioSnapshot
    
    today = date.today()
    
    # Check if snapshot exists for today
    existing_snapshot = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == current_user.id,
        PortfolioSnapshot.snapshot_date == today
    ).first()
    
    if not existing_snapshot:
        # Create new snapshot
        new_snapshot = PortfolioSnapshot(
            user_id=current_user.id,
            snapshot_date=today,
            total_equity=total_equity,
            total_profit=total_profit_val,
            total_earnings=total_earnings_12m,
            rentability_pct=total_profit_pct
        )
        db.add(new_snapshot)
        db.commit()
    else:
        # Update existing snapshot (in case values changed during the day)
        existing_snapshot.total_equity = total_equity
        existing_snapshot.total_profit = total_profit_val
        existing_snapshot.total_earnings = total_earnings_12m
        existing_snapshot.rentability_pct = total_profit_pct
        db.commit()
        
    # Fetch History (Last 30 days)
    history_records = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == current_user.id
    ).order_by(PortfolioSnapshot.snapshot_date.asc()).limit(30).all()
    
    history_data = {
        "dates": [h.snapshot_date.strftime("%d/%m") for h in history_records],
        "equity": [h.total_equity for h in history_records],
        "profit": [h.total_profit for h in history_records],
        "earnings": [h.total_earnings for h in history_records],
        "rentability": [h.rentability_pct for h in history_records]
    }

    # --- Agenda de Proventos (Real Data) ---
    today_date = date.today()
    agenda_data = []
    
    asset_ids = [item.asset_id for item in portfolio_items] if portfolio_items else []
    
    if asset_ids:
        # Fetch future dividends (and maybe recent past like last 30 days context?)
        # Let's show upcoming for now as per "Agenda"
        future_events = db.query(DividendEvent).filter(
            DividendEvent.asset_id.in_(asset_ids),
            DividendEvent.pay_date >= today_date
        ).order_by(DividendEvent.pay_date.asc()).limit(20).all()
        
        for ev in future_events:
            # Find associated portfolio item to get quantity
            p_item = next((i for i in portfolio_items if i.asset_id == ev.asset_id), None)
            if p_item and p_item.asset:
                total_recv = ev.amount * p_item.quantity
                agenda_data.append({
                    "ticker": p_item.asset.ticker,
                    "type": ev.type,
                    "pay_date": ev.pay_date.strftime("%d/%m/%Y"),
                    "record_date": ev.record_date.strftime("%d/%m/%Y") if ev.record_date else "-",
                    "amount": ev.amount,
                    "total_receive": total_recv,
                    "asset_type": p_item.asset.type
                })

    return {
        "equity": total_equity,
        "total_cost": total_cost,
        "total_profit": total_profit_val,
        "total_profit_pct": total_profit_pct,
        "earnings_year": total_earnings_12m,
        "rentability": total_profit_pct, 
        "asset_count": asset_count,
        "chart_allocation": {
            "labels": chart_labels,
            "values": chart_values
        },
        "history": history_data,
        "agenda": agenda_data, # New Real Data
        "assets": sorted(assets_list, key=lambda x: x['total_value'], reverse=True),
        "recommendations": {
            "items": visible_recs,
            "hidden_count": hidden_count,
            "is_premium": current_user.is_premium
        },
        "subscription": sub_status
    }
