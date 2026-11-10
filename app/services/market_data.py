import httpx
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.dividend import DividendEvent
import asyncio
from datetime import datetime
import re

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
    ticker_list = [t.strip().upper().replace(".SA", "") for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return

    print(f"Fetching {len(ticker_list)} assets via Brapi (1 por 1)...")
    timeout = httpx.Timeout(15.0, connect=5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        for symbol in ticker_list:
            try:
                # Brapi Free endpoint (1 ticker por requisicao)
                url = f"https://brapi.dev/api/quote/{symbol}?fundamental=true&token={BRAPI_TOKEN}"
                r = await client.get(url)
                if r.status_code != 200:
                    print(f"Erro Brapi para {symbol}: {r.status_code}")
                    continue
                
                data = r.json()
                results = data.get('results', [])
                if not results:
                    continue
                
                item = results[0]
                price = item.get('regularMarketPrice') or 0.0
                vol = item.get('regularMarketVolume') or 0
                lpa = item.get('earningsPerShare')
                
                # Create or Get
                asset_obj = db.query(Asset).filter(Asset.ticker == symbol).first()
                if not asset_obj:
                    is_fii = "11" in symbol
                    asset_obj = Asset(
                        ticker=symbol,
                        name=item.get('longName') or item.get('shortName') or symbol,
                        type='fii' if is_fii else 'stock',
                        sector='Fundo Imobiliário' if is_fii else 'Outros'
                    )
                    db.add(asset_obj)
                
                if item.get('longName') or item.get('shortName'):
                    asset_obj.name = item.get('longName') or item.get('shortName')
                
                if price and price > 0:
                    asset_obj.price = price
                
                if lpa and lpa > 0:
                    asset_obj.lpa = lpa
                
                if asset_obj.vpa and asset_obj.vpa > 0 and price > 0:
                    asset_obj.p_vp = round(price / asset_obj.vpa, 2)
                
                if vol and vol > 0 and price > 0:
                    asset_obj.liquidity_avg_2m = float(vol * price)
                
                asset_obj.updated_at = datetime.now()
                db.commit()
                print(f"[OK] Atualizado {symbol}: R$ {price}")
                
            except Exception as e:
                db.rollback()
                print(f"Erro ao processar {symbol}: {e}")

import re

async def scrape_investidor10(ticker: str, asset_type: str = 'fii'):
    """
    Scrapes basic FII/Stock data from Investidor10.
    asset_type: 'fii' or 'stock' (default 'fii' for compatibility)
    """
    base_path = "fiis" if asset_type == 'fii' else "acoes"
    url = f"https://investidor10.com.br/{base_path}/{ticker.lower()}/"
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
            
            # --- Extract Dividends ---
            try:
                table_match = re.search(r'<table id="table-dividends-history"(.*?)</table>', html, re.DOTALL)
                if table_match:
                    table_html = table_match.group(1)
                    rows = re.findall(r'<tr.*?>(.*?)</tr>', table_html, re.DOTALL)
                    
                    dividend_list = []
                    
                    for row in rows:
                        cols = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
                        clean_cols = [re.sub(r'<[^>]+>', '', c).strip() for c in cols]
                        if len(clean_cols) >= 4:
                            # 0: Tipo, 1: Data COM, 2: Pagamento, 3: Valor
                            d_type = clean_cols[0].upper()
                            d_datacom_str = clean_cols[1]
                            d_pay_str = clean_cols[2]
                            d_val_str = clean_cols[3]
                            
                            # Parse Value
                            try:
                                d_val = float(d_val_str.replace(",", "."))
                            except:
                                continue
                                
                            # Parse Dates
                            d_datacom = None
                            try:
                                if d_datacom_str != '-':
                                    d_datacom = datetime.strptime(d_datacom_str, "%d/%m/%Y").date()
                            except:
                                pass
                                
                            d_pay = None
                            try:
                                if d_pay_str != '-':
                                    d_pay = datetime.strptime(d_pay_str, "%d/%m/%Y").date()
                            except:
                                pass
                            
                            if d_pay: 
                                dividend_list.append({
                                    "type": d_type,
                                    "record_date": d_datacom,
                                    "pay_date": d_pay,
                                    "amount": d_val
                                })

                    if dividend_list:
                        data['dividends'] = dividend_list
            except Exception as e:
                print(f"Error extracting dividends for {ticker}: {e}")

            return data
            
        except Exception as e:
            print(f"Error scraping {ticker}: {e}")
            return None

