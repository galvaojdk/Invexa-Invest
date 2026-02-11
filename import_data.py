import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# Garantir que o diretório raiz está no path para importar os módulos do app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.core import database
# Importar todos os modelos para evitar erros de relacionamento do SQLAlchemy
from app.models import user, asset, portfolio, transaction, user_target
from app.models.dividend import DividendEvent
from app.models.alert import Alert
from app.models.setting import Setting
from app.services.transaction_service import TransactionService

# Dados fornecidos pelo usuário
raw_data = [
    ("SPXB11", "braetfs", "Compra", 10.0, 15.97, "21/01/2026"),
    ("PATL11", "fii", "Compra", 2.0, 67.05, "21/01/2026"),
    ("ALZR11", "fii", "Compra", 3.0, 10.70, "21/01/2026"),
    ("HGLG11", "fii", "Venda", 3.0, 156.76, "09/01/2026"),
    ("PORD11", "fii", "Compra", 1.0, 8.04, "09/01/2026"),
    ("PATL11", "fii", "Compra", 7.0, 67.82, "09/01/2026"),
    ("PETR4", "stock", "Compra", 4.0, 30.67, "29/12/2025"),
    ("SPXB11", "braetfs", "Compra", 12.0, 16.92, "29/12/2025"),
    ("ITSA4", "stock", "Compra", 9.0, 11.68, "12/12/2025"),
    ("PETR4", "stock", "Compra", 2.0, 31.42, "11/12/2025"),
    ("PETR4", "stock", "Compra", 7.0, 31.80, "11/12/2025"),
    ("ITSA4", "stock", "Compra", 20.0, 12.30, "09/12/2025"),
    ("BBAS3", "stock", "Compra", 5.0, 21.15, "09/12/2025"),
    ("ITUB4", "stock", "Compra", 5.0, 40.98, "09/12/2025"),
    ("GGRC11", "fii", "Compra", 30.0, 9.85, "08/12/2025"),
    ("ITUB4", "stock", "Compra", 8.0, 41.75, "08/12/2025"),
    ("XPLG11", "fii", "Compra", 3.0, 103.60, "08/12/2025"),
    ("PORD11", "fii", "Compra", 13.0, 7.96, "08/12/2025"),
    ("HGLG11", "fii", "Compra", 3.0, 161.60, "08/12/2025"),
    ("PORD11", "fii", "Compra", 13.0, 7.99, "05/12/2025"),
    ("ISAE4", "stock", "Compra", 11.0, 26.80, "05/12/2025"),
    ("GARE11", "fii", "Compra", 11.0, 9.07, "05/12/2025"),
    ("BBAS3", "stock", "Compra", 11.0, 21.37, "05/12/2025"),
    ("ALZR11", "fii", "Compra", 30.0, 10.74, "05/12/2025"),
]

def import_data(user_email: str):
    db = database.SessionLocal()
    
    # Buscar usuário
    target_user = db.query(user.User).filter(user.User.email == user_email).first()
    if not target_user:
        print(f"ERRO: Usuário com email '{user_email}' não encontrado no banco.")
        db.close()
        return

    print(f"--- Iniciando Importação para: {user_email} ---")
    
    success_count = 0
    for ticker, category, raw_type, qty, price, date_str in raw_data:
        # Converter tipos e datas
        t_type = "BUY" if raw_type.upper() == "COMPRA" else "SELL"
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        
        try:
            TransactionService.process_transaction(
                db=db,
                user_id=target_user.id,
                ticker=ticker,
                type=t_type,
                quantity=int(qty),
                price=float(price),
                date=date_obj,
                asset_type=category.lower()
            )
            print(f"[OK] {ticker} | {raw_type} | {int(qty)} un | R$ {price} | Data: {date_str}")
            success_count += 1
        except Exception as e:
            print(f"[ERRO] Falha ao importar {ticker}: {e}")

    db.close()
    print(f"--- Importação Finalizada: {success_count}/{len(raw_data)} transações processadas ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("DICA: Use o email que você usa para logar no Invexa.")
        print("Uso: python import_data.py seu@email.com")
    else:
        import_data(sys.argv[1])
