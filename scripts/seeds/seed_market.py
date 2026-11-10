import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import asyncio
from sqlalchemy.orm import Session
from app.core import database
from app.models.asset import Asset
from app.services.market_data import fetch_batch_brapi
import sys

# Lista de ativos para monitorar (Top B3)
TICKERS = [
    # Acoes (IBOVESPA Selection)
    "WEGE3.SA", "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBAS3.SA", 
    "BBDC4.SA", "RENT3.SA", "PRIO3.SA", "EGIE3.SA", "TAEE11.SA",
    "ABEV3.SA", "AZUL4.SA", "B3SA3.SA", "BBSE3.SA", "BPAC11.SA",
    "CMIG4.SA", "CSAN3.SA", "CSNA3.SA", "CVCB3.SA", "CYRE3.SA",
    "ELET3.SA", "EMBR3.SA", "EQTL3.SA", "GGBR4.SA", "GOAU4.SA",
    "HAPV3.SA", "HYPE3.SA", "JBSS3.SA", "KLBN11.SA", "LREN3.SA",
    "MGLU3.SA", "MRFG3.SA", "NTCO3.SA", "PETR3.SA", "RADL3.SA",
    "RAIL3.SA", "SBSP3.SA", "SUZB3.SA", "TOTS3.SA", "UGPA3.SA",
    "USIM5.SA", "VBBR3.SA", "VIVT3.SA", "YDUQ3.SA",
    
    # FIIs (IFIX Selection)
    "HGLG11.SA", "KNIP11.SA", "MXRF11.SA", "VISC11.SA", "XPLG11.SA",
    "BTLG11.SA", "CPTS11.SA", "BCFF11.SA", "HGRU11.SA", "IRDM11.SA",
    "ALZR11.SA", "BRCO11.SA", "BRCR11.SA", "DEVA11.SA", "GAME11.SA",
    "GGRC11.SA", "HCTR11.SA", "HGBS11.SA", "HGCR11.SA", "HGRE11.SA",
    "JSRE11.SA", "KNHY11.SA", "KNRI11.SA", "MALL11.SA", "RBRP11.SA",
    "RBRR11.SA", "RECR11.SA", "TGAR11.SA", "TRXF11.SA", "VILG11.SA",
    "VINC11.SA", "VINO11.SA", "VRTA11.SA", "VSLH11.SA", "XPML11.SA"
]

CHUNK_SIZE = 15

async def update_assets():
    db = database.SessionLocal()
    print("Iniciando atualizacao de ativos via Brapi...")
    
    # Criar tabelas se nao existirem (caso seja rodado antes do app)
    from app.models import user, asset, portfolio
    asset.Base.metadata.create_all(bind=database.engine)
    
    try:
        # Prepara lista limpa
        clean_tickers = [t.replace(".SA", "") for t in TICKERS]
        
        # Processa em chunks
        import math
        total = len(clean_tickers)
        print(f"Total de ativos para processar: {total}")
        
        for i in range(0, total, CHUNK_SIZE):
            chunk = clean_tickers[i:min(i + CHUNK_SIZE, total)]
            chunk_str = ",".join(chunk)
            print(f"Solicitando batch {i}-{i+len(chunk)}: {chunk_str}...")
            
            await fetch_batch_brapi(db, chunk_str)
            # Fetch batch ja faz o commit
            
    except Exception as e:
        print(f"Erro critical: {e}")
    finally:
        db.close()
        print("Atualizacao concluida.")

if __name__ == "__main__":
    asyncio.run(update_assets())
