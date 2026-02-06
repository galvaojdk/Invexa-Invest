from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core import database, security
from app.models.asset import Asset
from app.schemas import AssetResponse

router = APIRouter()

@router.get("/", response_model=List[AssetResponse])
def read_assets(skip: int = 0, limit: int = 100, asset_type: str = None, db: Session = Depends(database.get_db)):
    query = db.query(Asset)
    if asset_type:
        query = query.filter(Asset.type == asset_type)
    assets = query.offset(skip).limit(limit).all()
    
    # Valuation Logic (Runtime)
    for asset in assets:
        # Initialize runtime attrs prevents AttributeError
        asset.status = None
        asset.fair_price_graham = 0.0
        asset.fair_price_bazin = 0.0
        asset.safe_margin = 0.0
        
        # Graham (Acoes) - V = Sqrt(22.5 * LPA * VPA)
        if asset.type == 'stock' and asset.lpa > 0 and asset.vpa > 0:
            try:
                fair_price = (22.5 * asset.lpa * asset.vpa) ** 0.5
                asset.fair_price_graham = round(fair_price, 2)
                
                # Margem de Seguranca
                if fair_price > 0:
                    asset.safe_margin = round(((fair_price - asset.price) / fair_price) * 100, 1)
                
                if asset.price < fair_price:
                    asset.status = "Descontado"
                else:
                    asset.status = "Caro"
            except:
                pass
        
        # Bazin (FIIs/Dividend Stocks) - V = DY / 0.06
        # Considerando DY projected = DY_12m como proxy
        if asset.dy_12m and asset.dy_12m > 0:
             dividend_val = (asset.price * (asset.dy_12m / 100))
             fair_price_bazin = dividend_val / 0.06
             asset.fair_price_bazin = round(fair_price_bazin, 2)
             
             # If FII, use Bazin as primary 'Fair Price' for status and margin
             if asset.type == 'fii':
                 if fair_price_bazin > 0:
                     asset.safe_margin = round(((fair_price_bazin - asset.price) / fair_price_bazin) * 100, 1)
                     
                 if asset.price < fair_price_bazin:
                     asset.status = "Descontado"
                 else:
                     asset.status = "Neutro" # Or Caro?
                     
             # If Stock and not already set by Graham (fallback)
             elif not asset.status and asset.fair_price_bazin > asset.price:
                 asset.status = "Bom Pagador"
                 
    return assets
