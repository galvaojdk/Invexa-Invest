from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from app.core import database, security
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.asset import Asset
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
        
        # Valores
        current_val = item.quantity * asset.price
        cost_val = item.quantity * item.average_price
        
        total_equity += current_val
        total_cost += cost_val
        
        # Lucro/Prejuizo Item
        profit = current_val - cost_val
        profit_pct = (profit / cost_val * 100) if cost_val > 0 else 0.0
        
        # Proventos (Estimativa 12m baseada no DY)
        # DY é anual. Valor bruto anual = Valor investido (ou atual?) * DY.
        # Geralmente DY é sobre preço atual.
        yearly_earnings = current_val * (asset.dy_12m / 100)
        total_earnings_12m += yearly_earnings
        
        # Alocação por Tipo
        asset_type = asset.type or "Outros"
        # Normalizar label
        type_label = "Ações" if asset_type == "stock" else "FIIs" if asset_type == "fii" else asset_type.title()
        type_allocation[type_label] = type_allocation.get(type_label, 0) + current_val
        
        # Dados para Tabela
        assets_list.append({
            "ticker": asset.ticker,
            "quantity": item.quantity,
            "average_price": item.average_price,
            "current_price": asset.price,
            "total_value": current_val,
            "profit_val": profit,
            "profit_pct": profit_pct,
            "wallet_pct": 0, # Calc after total
            "recommendation": "Neutro" # Placeholder
        })


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
        delta = current_user.subscription_end_date - datetime.now()
        sub_status["days_remaining"] = delta.days
        sub_status["end_date"] = current_user.subscription_end_date.strftime("%d/%m/%Y")

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
        "assets": sorted(assets_list, key=lambda x: x['total_value'], reverse=True),
        "recommendations": {
            "items": visible_recs,
            "hidden_count": hidden_count,
            "is_premium": is_premium
        },
        "subscription": sub_status
    }
