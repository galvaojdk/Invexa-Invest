from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core import database
from app.models.user import User
from app.models.alert import Alert
from app.schemas import AlertCreate, AlertResponse
from app.api.routes.dashboard import get_current_active_user
from app.services import market_data

router = APIRouter()

# --- Dependencies ---
# Ensure user is Premium for some features
from datetime import datetime

async def get_current_premium_user(current_user: User = Depends(get_current_active_user), db: Session = Depends(database.get_db)):
    # Check if admin (bypass)
    if current_user.is_admin:
        return current_user

    # Check status and expiration
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recurso exclusivo para assinantes Premium"
        )
    
    # Check Expiration
    if current_user.subscription_end_date and current_user.subscription_end_date < datetime.now():
        # Expired! Update DB
        current_user.is_premium = False
        current_user.subscription_status = 'expired'
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sua assinatura expirou. Renove para continuar acessando."
        )
        
    return current_user

# --- Comparator (Freemium logic handled in frontend/backend mix) ---
@router.get("/comparator")
def compare_assets(tickers: str, db: Session = Depends(database.get_db), current_user: User = Depends(get_current_active_user)):
    """
    Receives comma-separated tickers. Returns fundamental data for comparison.
    If user is NOT premium, limit to 2 assets? Or just return data and let frontend blur?
    Let's limit to 2 for Free, unlimited for Premium.
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    
    if not current_user.is_premium and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Recurso exclusivo para assinantes Premium.")
            
    results = []
    for ticker in ticker_list:
        asset = market_data.get_or_create_asset(db, ticker)
        if asset:
            # Calculate metrics
            fair_graham = (22.5 * asset.lpa * asset.vpa) ** 0.5 if (asset.lpa > 0 and asset.vpa > 0) else 0.0
            
            # Smart Dividend Yield (Use 12m)
            dy = asset.dy_12m
            fair_bazin = (asset.price * (dy/100)) / 0.06 if dy > 0 else 0.0 # Just a reversed calc? No, Bazin is Div/0.06 = Fair Price.
            # Wait, Bazin Price = Dividend / 0.06.
            # Dividend Amount = Price * DY.
            div_val = asset.price * (dy / 100)
            fair_bazin = div_val / 0.06 if div_val > 0 else 0.0

            results.append({
                "ticker": asset.ticker,
                "price": asset.price,
                "dy": asset.dy_12m,
                "p_vp": asset.p_vp,
                "lpa": asset.lpa,
                "vpa": asset.vpa,
                "sector": asset.sector,
                "fair_graham": round(fair_graham, 2),
                "fair_bazin": round(fair_bazin, 2),
                "net_income": asset.net_income,
                "roe": (asset.lpa / asset.vpa * 100) if asset.vpa > 0 else 0.0 # ROE Est
            })
            
    return results

# --- Alerts (Premium Only) ---
@router.post("/alerts", response_model=AlertResponse)
def create_alert(
    alert: AlertCreate, 
    db: Session = Depends(database.get_db), 
    current_user: User = Depends(get_current_premium_user)
):
    # Check limit?
    count = db.query(Alert).filter(Alert.user_id == current_user.id).count()
    if count >= 20: 
         raise HTTPException(status_code=400, detail="Limite de alertas atingido.")

    new_alert = Alert(
        user_id=current_user.id,
        ticker=alert.ticker.upper(),
        type=alert.type,
        target_price=alert.target_price
    )
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    return new_alert

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(
    db: Session = Depends(database.get_db), 
    current_user: User = Depends(get_current_premium_user)
):
    return db.query(Alert).filter(Alert.user_id == current_user.id).all()

# --- Valuation (Premium Only) ---
@router.get("/valuation/{ticker}")
def get_valuation(
    ticker: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_premium_user)
):
    asset = market_data.get_or_create_asset(db, ticker)
    if not asset:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")

    # Validar campos nulos
    price = asset.price if asset.price else 0.0
    lpa = asset.lpa if asset.lpa else 0.0
    vpa = asset.vpa if asset.vpa else 0.0
    dy_12m = asset.dy_12m if asset.dy_12m else 0.0

    # Formula de Graham: V = Sqrt(22.5 * LPA * VPA)
    # Graham não se aplica a FIIs (LPA/VPA distorcidos) ou empresas com prejuízo (LPA < 0)
    fair_graham = None
    if asset.type != 'fii' and lpa > 0 and vpa > 0:
        fair_graham = (22.5 * lpa * vpa) ** 0.5

    # Metodo de Bazin: Preço Justo = Dividend Yield Médio / 0.06
    # Usando DY atual como proxy do 'Yield Médio' (Limitação do MVP)
    # Ou: Preço Teto = DPA / 0.06. 
    # DPA (Dividendo por Ação) = Price * (DY/100)
    dpa = price * (dy_12m / 100)
    fair_bazin = dpa / 0.06 if dpa > 0 else 0.0

    # Margem de Segurança (Graham)
    margin_graham = 0.0
    if fair_graham and fair_graham > 0 and price > 0:
        margin_graham = ((fair_graham - price) / fair_graham) * 100

    return {
        "ticker": asset.ticker,
        "price": price,
        "graham": {
            "fair_price": round(fair_graham, 2) if fair_graham else None,
            "margin": round(margin_graham, 2) if fair_graham else None
        },
        "bazin": {
            "fair_price": round(fair_bazin, 2),
            "dividend_per_share": round(dpa, 2)
        },
        "indicators": {
            "lpa": lpa,
            "vpa": vpa,
            "dy": dy_12m
        }
    }

# --- Calendar (Premium Only) ---
from app.models.portfolio import Portfolio
import random
from datetime import datetime, timedelta

@router.get("/calendar")
def get_dividend_calendar(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_premium_user)
):
    # Fetch User Portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    
    total_monthly_est = 0.0
    upcoming_events = []
    
    for item in portfolio:
        asset = item.asset
        if asset and asset.dy_12m > 0:
            # Estimate Annual Income
            annual_income = (asset.price * (asset.dy_12m / 100)) * item.quantity
            total_monthly_est += annual_income / 12
            
            # Mock Upcoming Payment (MVP)
            # In real app, we would query a 'Dividend' table
            days_offset = random.randint(5, 45)
            pay_date = datetime.now() + timedelta(days=days_offset)
            
            upcoming_events.append({
                "ticker": asset.ticker,
                "amount": round(annual_income / 4, 2), # Assuming quarterly
                "pay_date": pay_date.strftime("%d/%m/%Y"),
                "type": "Dividendo"
            })
            
    # Sort events
    upcoming_events.sort(key=lambda x: datetime.strptime(x['pay_date'], "%d/%m/%Y"))
    
    return {
        "monthly_estimate": round(total_monthly_est, 2),
        "total_annual_estimate": round(total_monthly_est * 12, 2),
        "events": upcoming_events
    }
