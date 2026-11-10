from app.core.database import SessionLocal, engine
from sqlalchemy import text
import sys
import os

# Adiciona o diretório raiz (app) ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def fix_price_nullable():
    # Usar engine.begin() para garantir commit da transação
    with engine.begin() as con:
        try:
            # PostgreSQL: Alterar coluna PRICE para permitir NULL
            con.execute(text("ALTER TABLE assets ALTER COLUMN price DROP NOT NULL"))
            print("SUCESSO: Coluna 'price' agora aceita valores NULL.")
            
            # Verificação
            result = con.execute(text("SELECT is_nullable FROM information_schema.columns WHERE table_name = 'assets' AND column_name = 'price'"))
            row = result.fetchone()
            print(f"VERIFICAÇÃO: is_nullable = {row[0]}")
            
        except Exception as e:
            print(f"ERRO: {e}")

if __name__ == "__main__":
    fix_price_nullable()
