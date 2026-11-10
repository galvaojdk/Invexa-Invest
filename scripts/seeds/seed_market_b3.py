import sys
import os
from datetime import date, datetime, timedelta

# Adiciona a raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import app.models
from app.core import database
from app.models.asset import Asset
from app.models.dividend import DividendEvent

MARKET_DATA = [
    # --- AÇÕES IBOVESPA (B3) ---
    {
        "ticker": "PETR4", "name": "Petrobras PN", "type": "stock", "sector": "Energia",
        "price": 45.23, "dy_12m": 14.8, "p_vp": 1.21, "lpa": 10.35, "vpa": 37.32,
        "liquidity_avg_2m": 850000000.0, "payment_months": "2,5,8,11",
        "div_amount": 1.45, "div_type": "DIVIDEND"
    },
    {
        "ticker": "VALE3", "name": "Vale ON", "type": "stock", "sector": "Materiais Básicos",
        "price": 64.24, "dy_12m": 8.9, "p_vp": 1.42, "lpa": 6.80, "vpa": 45.10,
        "liquidity_avg_2m": 620000000.0, "payment_months": "3,9",
        "div_amount": 2.10, "div_type": "DIVIDEND"
    },
    {
        "ticker": "WEGE3", "name": "WEG ON", "type": "stock", "sector": "Industriais",
        "price": 51.58, "dy_12m": 2.6, "p_vp": 12.05, "lpa": 1.49, "vpa": 4.28,
        "liquidity_avg_2m": 180000000.0, "payment_months": "3,8,12",
        "div_amount": 0.35, "div_type": "DIVIDEND"
    },
    {
        "ticker": "BBAS3", "name": "Banco do Brasil ON", "type": "stock", "sector": "Financeiro",
        "price": 28.50, "dy_12m": 9.5, "p_vp": 0.80, "lpa": 5.90, "vpa": 35.80,
        "liquidity_avg_2m": 380000000.0, "payment_months": "3,6,9,12",
        "div_amount": 0.85, "div_type": "JCP"
    },
    {
        "ticker": "ITUB4", "name": "Itaú Unibanco PN", "type": "stock", "sector": "Financeiro",
        "price": 36.80, "dy_12m": 6.2, "p_vp": 1.71, "lpa": 3.75, "vpa": 21.50,
        "liquidity_avg_2m": 460000000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.25, "div_type": "JCP"
    },
    {
        "ticker": "BBDC4", "name": "Bradesco PN", "type": "stock", "sector": "Financeiro",
        "price": 14.90, "dy_12m": 6.8, "p_vp": 0.87, "lpa": 1.65, "vpa": 17.20,
        "liquidity_avg_2m": 290000000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.12, "div_type": "JCP"
    },
    {
        "ticker": "TAEE11", "name": "Taesa Unit", "type": "stock", "sector": "Utilidade Pública",
        "price": 36.40, "dy_12m": 10.4, "p_vp": 1.58, "lpa": 3.40, "vpa": 23.10,
        "liquidity_avg_2m": 75000000.0, "payment_months": "5,8,11,12",
        "div_amount": 0.98, "div_type": "DIVIDEND"
    },
    {
        "ticker": "EGIE3", "name": "Engie Brasil ON", "type": "stock", "sector": "Utilidade Pública",
        "price": 42.10, "dy_12m": 7.8, "p_vp": 2.66, "lpa": 3.60, "vpa": 15.80,
        "liquidity_avg_2m": 65000000.0, "payment_months": "5,8,11",
        "div_amount": 1.25, "div_type": "DIVIDEND"
    },
    {
        "ticker": "CMIG4", "name": "Cemig PN", "type": "stock", "sector": "Utilidade Pública",
        "price": 11.80, "dy_12m": 11.2, "p_vp": 0.96, "lpa": 2.10, "vpa": 12.30,
        "liquidity_avg_2m": 95000000.0, "payment_months": "4,6,12",
        "div_amount": 0.45, "div_type": "JCP"
    },
    {
        "ticker": "BBSE3", "name": "BB Seguridade ON", "type": "stock", "sector": "Financeiro",
        "price": 35.20, "dy_12m": 8.9, "p_vp": 4.69, "lpa": 3.85, "vpa": 7.50,
        "liquidity_avg_2m": 120000000.0, "payment_months": "3,8",
        "div_amount": 1.40, "div_type": "DIVIDEND"
    },
    {
        "ticker": "ABEV3", "name": "Ambev ON", "type": "stock", "sector": "Consumo Não Cíclico",
        "price": 12.60, "dy_12m": 6.5, "p_vp": 2.07, "lpa": 0.95, "vpa": 6.10,
        "liquidity_avg_2m": 210000000.0, "payment_months": "12",
        "div_amount": 0.73, "div_type": "JCP"
    },
    {
        "ticker": "KLBN11", "name": "Klabin Unit", "type": "stock", "sector": "Materiais Básicos",
        "price": 22.30, "dy_12m": 7.4, "p_vp": 1.21, "lpa": 2.10, "vpa": 18.40,
        "liquidity_avg_2m": 85000000.0, "payment_months": "2,5,8,11",
        "div_amount": 0.42, "div_type": "DIVIDEND"
    },
    {
        "ticker": "GGBR4", "name": "Gerdau PN", "type": "stock", "sector": "Materiais Básicos",
        "price": 18.90, "dy_12m": 6.1, "p_vp": 0.72, "lpa": 2.45, "vpa": 26.20,
        "liquidity_avg_2m": 105000000.0, "payment_months": "3,6,9,12",
        "div_amount": 0.38, "div_type": "DIVIDEND"
    },
    {
        "ticker": "CSNA3", "name": "Siderúrgica Nacional ON", "type": "stock", "sector": "Materiais Básicos",
        "price": 11.20, "dy_12m": 7.5, "p_vp": 0.72, "lpa": 1.80, "vpa": 15.60,
        "liquidity_avg_2m": 90000000.0, "payment_months": "5,11",
        "div_amount": 0.35, "div_type": "DIVIDEND"
    },
    {
        "ticker": "VIVT3", "name": "Telefônica Brasil ON", "type": "stock", "sector": "Comunicação",
        "price": 52.40, "dy_12m": 7.6, "p_vp": 1.25, "lpa": 3.25, "vpa": 41.80,
        "liquidity_avg_2m": 115000000.0, "payment_months": "4,7,10,12",
        "div_amount": 1.15, "div_type": "JCP"
    },
    {
        "ticker": "ITSA4", "name": "Itaúsa PN", "type": "stock", "sector": "Financeiro",
        "price": 10.40, "dy_12m": 8.3, "p_vp": 1.13, "lpa": 1.45, "vpa": 9.20,
        "liquidity_avg_2m": 155000000.0, "payment_months": "1,3,4,6,7,9,10,12",
        "div_amount": 0.22, "div_type": "JCP"
    },

    # --- FUNDOS IMOBILIÁRIOS IFIX (B3) ---
    {
        "ticker": "MXRF11", "name": "Maxi Renda FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 8.85, "dy_12m": 12.4, "p_vp": 0.98, "lpa": 1.15, "vpa": 9.03,
        "liquidity_avg_2m": 14000000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.09, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "HGLG11", "name": "CSHG Logística FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 145.56, "dy_12m": 9.6, "p_vp": 0.95, "lpa": 14.80, "vpa": 153.20,
        "liquidity_avg_2m": 9500000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 1.10, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "XPLG11", "name": "XP Log FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 96.80, "dy_12m": 9.8, "p_vp": 0.88, "lpa": 9.85, "vpa": 110.00,
        "liquidity_avg_2m": 6200000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.78, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "BTLG11", "name": "BTG Pactual Logística FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 98.50, "dy_12m": 9.7, "p_vp": 0.96, "lpa": 9.90, "vpa": 102.60,
        "liquidity_avg_2m": 8100000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.78, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "KNIP11", "name": "Kinea Rendimentos Imobiliários FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 88.40, "dy_12m": 11.8, "p_vp": 0.92, "lpa": 10.80, "vpa": 96.10,
        "liquidity_avg_2m": 11000000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.85, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "VISC11", "name": "Vinci Shopping Centers FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 108.20, "dy_12m": 9.2, "p_vp": 0.87, "lpa": 10.20, "vpa": 124.40,
        "liquidity_avg_2m": 7300000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.80, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "XPML11", "name": "XP Malls FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 102.40, "dy_12m": 9.4, "p_vp": 0.91, "lpa": 9.90, "vpa": 112.50,
        "liquidity_avg_2m": 12500000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.82, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "CPTS11", "name": "Capitânia Securities II FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 7.90, "dy_12m": 13.1, "p_vp": 0.89, "lpa": 1.05, "vpa": 8.88,
        "liquidity_avg_2m": 9200000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.08, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "HGRU11", "name": "CSHG Renda Urbana FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 121.50, "dy_12m": 9.5, "p_vp": 0.97, "lpa": 12.10, "vpa": 125.30,
        "liquidity_avg_2m": 5100000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.90, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "IRDM11", "name": "Iridium Recebíveis Imobiliários FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 69.80, "dy_12m": 13.8, "p_vp": 0.82, "lpa": 9.80, "vpa": 85.10,
        "liquidity_avg_2m": 6100000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.75, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "ALZR11", "name": "Alianza Trust Renda Imobiliária FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 104.30, "dy_12m": 9.3, "p_vp": 0.98, "lpa": 9.80, "vpa": 106.40,
        "liquidity_avg_2m": 4200000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.82, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "TGAR11", "name": "TG Ativo Real FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 114.20, "dy_12m": 14.2, "p_vp": 0.94, "lpa": 16.50, "vpa": 121.50,
        "liquidity_avg_2m": 4800000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 1.35, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "TRXF11", "name": "TRX Real Estate FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 103.80, "dy_12m": 10.2, "p_vp": 0.99, "lpa": 10.80, "vpa": 104.90,
        "liquidity_avg_2m": 5800000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.90, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "VRTA11", "name": "Fator Veritá FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 85.60, "dy_12m": 11.5, "p_vp": 0.91, "lpa": 10.20, "vpa": 94.10,
        "liquidity_avg_2m": 3900000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.80, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "KNRI11", "name": "Kinea Renda Imobiliária FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 148.90, "dy_12m": 8.8, "p_vp": 0.93, "lpa": 13.50, "vpa": 160.10,
        "liquidity_avg_2m": 7200000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 1.05, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "HGBS11", "name": "Hedge Brasil Shopping FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 208.50, "dy_12m": 8.9, "p_vp": 0.92, "lpa": 19.20, "vpa": 226.60,
        "liquidity_avg_2m": 4500000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 1.50, "div_type": "RENDIMENTO"
    },
    {
        "ticker": "GGRC11", "name": "GGR Covepi Renda FII", "type": "fii", "sector": "Fundo Imobiliário",
        "price": 11.10, "dy_12m": 10.8, "p_vp": 0.95, "lpa": 1.25, "vpa": 11.68,
        "liquidity_avg_2m": 3400000.0, "payment_months": "1,2,3,4,5,6,7,8,9,10,11,12",
        "div_amount": 0.10, "div_type": "RENDIMENTO"
    }
]

def seed_market_data():
    db = database.SessionLocal()
    try:
        # Garante que as tabelas existem
        database.Base.metadata.create_all(bind=database.engine)
        
        inserted = 0
        updated = 0
        today = date.today()
        
        for item in MARKET_DATA:
            ticker = item["ticker"]
            asset_obj = db.query(Asset).filter(Asset.ticker == ticker).first()
            if not asset_obj:
                asset_obj = Asset(ticker=ticker)
                db.add(asset_obj)
                inserted += 1
            else:
                updated += 1
            
            asset_obj.name = item["name"]
            asset_obj.type = item["type"]
            asset_obj.sector = item["sector"]
            asset_obj.price = item["price"]
            asset_obj.dy_12m = item["dy_12m"]
            asset_obj.p_vp = item["p_vp"]
            asset_obj.lpa = item["lpa"]
            asset_obj.vpa = item["vpa"]
            asset_obj.liquidity_avg_2m = item["liquidity_avg_2m"]
            asset_obj.payment_months = item["payment_months"]
            asset_obj.updated_at = datetime.now()
            
            db.flush()
            
            # Adiciona DividendEvent histórico recente e próximo
            if "div_amount" in item and item["div_amount"] > 0:
                # Checa se já existe evento recente
                has_div = db.query(DividendEvent).filter(DividendEvent.asset_id == asset_obj.id).first()
                if not has_div:
                    # Evento passado (mês anterior)
                    prev_pay = today - timedelta(days=20)
                    div_past = DividendEvent(
                        asset_id=asset_obj.id,
                        type=item["div_type"],
                        amount=item["div_amount"],
                        record_date=prev_pay - timedelta(days=7),
                        pay_date=prev_pay
                    )
                    db.add(div_past)
                    
                    # Próximo evento agendado (mês atual/próximo)
                    next_pay = today + timedelta(days=12)
                    div_future = DividendEvent(
                        asset_id=asset_obj.id,
                        type=item["div_type"],
                        amount=item["div_amount"],
                        record_date=today + timedelta(days=2),
                        pay_date=next_pay
                    )
                    db.add(div_future)

        db.commit()
        print(f"[OK] Carga de mercado concluída com sucesso!")
        print(f"     -> {inserted} ativos novos inseridos")
        print(f"     -> {updated} ativos existentes atualizados")
        print(f"     -> Total de ativos no banco: {db.query(Asset).count()}")
    except Exception as e:
        db.rollback()
        print(f"[ERRO] Falha ao popular dados de mercado: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_market_data()

