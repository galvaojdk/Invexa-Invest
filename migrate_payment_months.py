from app.core.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as con:
        try:
            con.execute(text("ALTER TABLE assets ADD COLUMN payment_months TEXT"))
            con.commit()
            print("Coluna 'payment_months' adicionada com sucesso.")
        except Exception as e:
            print(f"Erro (talvez já exista): {e}")

if __name__ == "__main__":
    migrate()
