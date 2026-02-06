from app.core.database import SessionLocal, engine
from sqlalchemy import text

def migrate():
    with engine.connect() as con:
        try:
            con.execute(text("ALTER TABLE assets ADD COLUMN shares_outstanding INTEGER DEFAULT 0"))
            print("Coluna 'shares_outstanding' adicionada com sucesso.")
        except Exception as e:
            print(f"Erro (talvez já exista): {e}")

if __name__ == "__main__":
    migrate()
