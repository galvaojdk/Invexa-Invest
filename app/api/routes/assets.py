from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core import database, security
from app.models.asset import Asset
from app.schemas import AssetResponse
from app.services.market_data import fetch_batch_brapi
import asyncio

# Hardcoded list of assets to seed/monitor (Top B3)
TICKERS = [
    # Acoes (IBOVESPA Selection)
    "WEGE3", "PETR4", "VALE3", "ITUB4", "BBAS3", 
    "BBDC4", "RENT3", "PRIO3", "EGIE3", "TAEE11",
    "ABEV3", "AZUL4", "B3SA3", "BBSE3", "BPAC11",
    "CMIG4", "CSAN3", "CSNA3", "CVCB3", "CYRE3",
    "ELET3", "EMBR3", "EQTL3", "GGBR4", "GOAU4",
    "HAPV3", "HYPE3", "JBSS3", "KLBN11", "LREN3",
    "MGLU3", "MRFG3", "NTCO3", "PETR3", "RADL3",
    "RAIL3", "SBSP3", "SUZB3", "TOTS3", "UGPA3",
    "USIM5", "VBBR3", "VIVT3", "YDUQ3",
    
    # FIIs (IFIX Selection)
    "HGLG11", "KNIP11", "MXRF11", "VISC11", "XPLG11",
    "BTLG11", "CPTS11", "BCFF11", "HGRU11", "IRDM11",
    "ALZR11", "BRCO11", "BRCR11", "DEVA11", "GAME11",
    "GGRC11", "HCTR11", "HGBS11", "HGCR11", "HGRE11",
    "JSRE11", "KNHY11", "KNRI11", "MALL11", "RBRP11",
    "RBRR11", "RECR11", "TGAR11", "TRXF11", "VILG11",
    "VINC11", "VINO11", "VRTA11", "VSLH11", "XPML11"
]

router = APIRouter()

@router.get("/", response_model=List[AssetResponse])
def read_assets(skip: int = 0, limit: int = 100, asset_type: str = None, db: Session = Depends(database.get_db)):
    if db.query(Asset).count() == 0:
        try:
            from scripts.seeds.seed_market_b3 import seed_market_data
            seed_market_data()
        except Exception as e:
            print(f"Erro no auto-seed de ativos: {e}")

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

@router.post("/update_all")
async def update_all_assets(db: Session = Depends(database.get_db)):
    """
    Triggers a full update of all monitored assets.
    Useful for seeding the database on first run.
    """
    print(f"Update All triggered. Processing {len(TICKERS)} assets...")
    
    # Process in chunks of 15 to respect Brapi limits/performance
    chunk_size = 15
    import math
    
    # Filter tickers that might already have the suffix (just in case)
    clean_tickers = [t.replace(".SA", "") for t in TICKERS]
    
    count = 0
    for i in range(0, len(clean_tickers), chunk_size):
        chunk = clean_tickers[i:min(i + chunk_size, len(clean_tickers))]
        chunk_str = ",".join(chunk)
        print(f"Updating batch: {chunk_str}...")
        
        try:
            # fetch_batch_brapi is async and handles DB commit
            await fetch_batch_brapi(db, chunk_str)
            count += len(chunk)
        except Exception as e:
            print(f"Error updating batch {chunk_str}: {e}")
            # Continue to next batch instead of crashing
            continue
        
    return {"status": "success", "message": f"Updated {count} assets"}
