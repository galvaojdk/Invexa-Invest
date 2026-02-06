from app.core.database import SessionLocal, engine
from sqlalchemy import text

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
