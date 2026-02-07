import httpx
from sqlalchemy.orm import Session
from app.models.asset import Asset
import asyncio

BRAPI_TOKEN = "5y8qbu4kibxgcT3YQxG1XK"

def update_all_assets(db: Session):
    """Atualiza dados de todos os ativos no banco usando Brapi."""
    assets = db.query(Asset).all()
    print(f"Atualizando {len(assets)} ativos via Brapi...")
    
    # Batch update is ideal but for now we iterate to keep logic simple
    # Or we can batch requests? Brapi supports comma separated.
    # Let's batch 20 at a time to reduce connection overhead.
    tickers = [a.ticker for a in assets]
    
    # Split into chunks of 15
    import math
    chunk_size = 15
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:min(i + chunk_size, len(tickers))]
        chunk_str = ",".join(chunk)
        asyncio.run(fetch_batch_brapi(db, chunk_str))
        
    return {"status": "ok", "updated": len(assets)}

def get_or_create_asset(db: Session, ticker: str):
    ticker_clean = ticker.upper().replace(".SA", "")
    asset = db.query(Asset).filter(Asset.ticker == ticker_clean).first()
    if asset:
        return asset
    # Single fetch
    asyncio.run(fetch_batch_brapi(db, ticker_clean))
    return db.query(Asset).filter(Asset.ticker == ticker_clean).first()

async def fetch_batch_brapi(db: Session, tickers: str):
    # Add modules to get rich data
    modules = "summaryProfile,defaultKeyStatistics,financialData"
    url = f"https://brapi.dev/api/quote/{tickers}?fundamental=true&modules={modules}&token={BRAPI_TOKEN}"
    print(f"Fetching batch via Brapi: {tickers}...")
    
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(url)
            if r.status_code != 200:
                print(f"Erro Brapi: {r.status_code} - {r.text}")
                return
                
            data = r.json()
            results = data.get('results', [])
            
            for item in results:
                symbol = item.get('symbol')
                price = item.get('regularMarketPrice') or 0.0
                
                # Modules
                dk_stats = item.get('defaultKeyStatistics') or {}
                sum_prof = item.get('summaryProfile') or {}
                fin_data = item.get('financialData') or {}
                
                # Create or Get
                asset_obj = db.query(Asset).filter(Asset.ticker == symbol).first()
                if not asset_obj:
                    asset_obj = Asset(ticker=symbol)
                    db.add(asset_obj)
                
                # Basic
                asset_obj.name = item.get('longName') or item.get('shortName') or symbol
                if price and price > 0:
                    asset_obj.price = price
                
                # Sector
                raw_sector = sum_prof.get('sector') or 'Outros'
                SECTOR_MAP = {
                    'Financial Services': 'Serviços Financeiros',
                    'Utilities': 'Utilidade Pública',
                    'Basic Materials': 'Materiais Básicos',
                    'Real Estate': 'Imobiliário',
                    'Energy': 'Energia',
                    'Industrials': 'Industriais',
                    'Consumer Defensive': 'Consumo Não Cíclico',
                    'Consumer Cyclical': 'Consumo Cíclico',
                    'Technology': 'Tecnologia',
                    'Healthcare': 'Saúde',
                    'Communication Services': 'Comunicação',
                    'Consumer Goods': 'Bens de Consumo'
                }
                asset_obj.sector = SECTOR_MAP.get(raw_sector, raw_sector)
                
                # Type Logic
                is_fii = "11" in symbol and (asset_obj.sector == 'Imobiliário' or "FUNDO" in asset_obj.name.upper())
                asset_obj.type = 'fii' if is_fii else 'stock'
                if is_fii and asset_obj.sector == 'Outros': asset_obj.sector = 'Fundo Imobiliário'
                
                # Extraction ----------------------
                
                # P/VP (Price to Book)
                # Usually in defaultKeyStatistics.priceToBook
                p_vp = dk_stats.get('priceToBook')
                if not p_vp:
                     # Fallback: Price / BookValue
                     bv = dk_stats.get('bookValue')
                     if bv and bv > 0 and price > 0:
                         p_vp = price / bv
                asset_obj.p_vp = p_vp or 0.0
                
                # LPA (EPS)
                lpa = dk_stats.get('trailingEps') or item.get('earningsPerShare') or 0.0
                asset_obj.lpa = lpa
                
                # VPA (Book Value)
                vpa = dk_stats.get('bookValue') or 0.0
                if vpa != 0:
                   asset_obj.vpa = vpa
                
                # Shares
                shares = dk_stats.get('sharesOutstanding') or dk_stats.get('impliedSharesOutstanding') or 0
                asset_obj.shares_outstanding = int(shares)
                
                # Net Income
                # Brapi dump showed no 'netIncomeToCommon'. 
                # Calc: EPS * Shares or ProfitMargin * Revenue
                net_income = dk_stats.get('netIncomeToCommon')
                if not net_income:
                    if lpa and shares:
                        net_income = lpa * shares
                    elif fin_data.get('profitMargins') and fin_data.get('totalRevenue'):
                         net_income = fin_data.get('profitMargins') * fin_data.get('totalRevenue')
                
                asset_obj.net_income = net_income or 0.0
                
                # Dividend Yield (12m)
                # Brapi dump: 'dividendYield': 2.63326 (in defaultKeyStatistics)
                # Check magnitude. If > 0.5 likely percent. If < 0.5 likely decimal? 
                # Actually dump said 2.63326. WEGE3 is around 2-3%. So it is PERCENT value.
                # Standard convention: 0.0263 (decimal).
                # But Brapi seems to send 2.63?
                # Let's verify dump again.
                # "dividendYield": 2.63326.
                # If it was decimal it would be 0.026.
                # So it IS percent.
                dy = dk_stats.get('dividendYield') or item.get('dividendYield') or 0.0
                # If value is like 0.05 (5%), keep it? Or is it 5.0?
                # If > 1.0 it is likely percent. If < 1.0 (and not 0), it might be decimal.
                # But careful. 2.63 is percent.
                # My DB likely stores percent (e.g. 2.63).
                # Previous logic: "if dy < 0.5 and dy > 0: dy = dy * 100".
                # If Brapi sends 2.63, it stays 2.63.
                # If Brapi sends 0.0263, it becomes 2.63.
                if dy > 0 and dy < 0.5:
                    dy = dy * 100
                
                # Fallback Investidor10 for FIIs if data is missing
                # FIIs often have Brapi fundamental data missing (DY=0, P/VP=0)
                # Also Check Price if Brapi failed (Price=0)
                if is_fii and (dy == 0 or p_vp == 0 or p_vp == 0.0 or price == 0):
                    print(f" -> Fetching extra data for FII {symbol} from Investidor10...")
                    extra_data = await scrape_investidor10(symbol)
                    if extra_data:
                        if dy == 0 and extra_data.get('dy'):
                            dy = extra_data['dy']
                        if p_vp == 0 and extra_data.get('p_vp'):
                            p_vp = extra_data['p_vp']
                        if price == 0 and extra_data.get('price'):
                            price = extra_data['price']
                        # Net Income is hard from I10 main page, but maybe Vacancy or other fields later.
                        
                if price and price > 0: asset_obj.price = price
                if dy and dy > 0: asset_obj.dy_12m = dy
                if p_vp and p_vp > 0: asset_obj.p_vp = p_vp
                
                # Liquidity (Financial Volume = Volume * Price)
                # averageDailyVolume3Month is usually in defaultKeyStatistics or summaryDetail
                # regularMarketVolume is in root
                vol = item.get('regularMarketVolume') or 0
                avg_vol_3m = dk_stats.get('averageDailyVolume3Month') or 0
                
                # Use 3M avg if available for stability, else daily volume
                used_vol = avg_vol_3m if avg_vol_3m > 0 else vol
                
                if used_vol and used_vol > 0 and asset_obj.price > 0:
                     asset_obj.liquidity_avg_2m = float(used_vol * asset_obj.price)
                
            db.commit()

        except Exception as e:
            print(f"Batch Error {tickers}: {e}")

import re

async def scrape_investidor10(ticker: str):
    """
    Scrapes basic FII data (DY, P/VP) from Investidor10 to supplement Brapi.
    """
    url = f"https://investidor10.com.br/fiis/{ticker.lower()}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                print(f"Investidor10 fetch failed {ticker}: {r.status_code}")
                return None
            
            html = r.text
            data = {}
            
            # DY
            dy_match = re.search(r'title="Dividend Yield".*?_card-body.*?<span>([\d,]+)%</span>', html, re.DOTALL)
            if dy_match:
                try:
                    data['dy'] = float(dy_match.group(1).replace(",", "."))
                except:
                    pass
            
            # P/VP
            pvp_match = re.search(r'P/VP</span>.*?_card-body.*?<span>([\d,]+)</span>', html, re.DOTALL)
            if pvp_match:
                 try:
                    data['p_vp'] = float(pvp_match.group(1).replace(",", "."))
                 except:
                    pass

            # Price (Cotação) fallback
            # Context: title="Cota..." ... _card-body... <span class="value">R$ 156,95</span>
            price_match = re.search(r'title="Cota.*?".*?_card-body.*?(?:class="value">|<span>)R\$\s*([\d,]+)', html, re.DOTALL)
            if price_match:
                 try:
                    data['price'] = float(price_match.group(1).replace(",", "."))
                 except:
                    pass
            
            return data
            
        except Exception as e:
            print(f"Error scraping {ticker}: {e}")
            return None

