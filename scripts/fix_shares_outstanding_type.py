from sqlalchemy import text
import sys
import os

# Adiciona o diretório raiz (app) ao sys.path para permitir importar 'app'
# Isso funciona tanto rodando scripts/local ou no container como /app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal, engine

def fix_migration():
    # Usar engine.begin() para garantir commit da transação
    with engine.begin() as con:
        try:
            # PostgreSQL: Alterar para BIGINT
            con.execute(text("ALTER TABLE assets ALTER COLUMN shares_outstanding TYPE BIGINT"))
            print("SUCESSO: Coluna 'shares_outstanding' alterada para BIGINT.")
            
            # Verificação
            result = con.execute(text("SELECT data_type FROM information_schema.columns WHERE table_name = 'assets' AND column_name = 'shares_outstanding'"))
            row = result.fetchone()
            print(f"VERIFICAÇÃO: Tipo atual da coluna: {row[0]}")
            
        except Exception as e:
            print(f"ERRO: {e}")

if __name__ == "__main__":
    fix_migration()
