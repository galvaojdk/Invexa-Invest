from sqlalchemy import text
import sys
import os

# Adiciona o diretório raiz (app) ao sys.path para permitir importar 'app'
# Isso funciona tanto rodando scripts/local ou no container como /app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal, engine

def fix_migration():
    with engine.connect() as con:
        try:
            # PostgreSQL syntax to alter column type
            con.execute(text("ALTER TABLE assets ALTER COLUMN shares_outstanding TYPE BIGINT"))
            print("Coluna 'shares_outstanding' alterada para BIGINT com sucesso.")
        except Exception as e:
            print(f"Erro ao alterar coluna: {e}")

if __name__ == "__main__":
    fix_migration()
