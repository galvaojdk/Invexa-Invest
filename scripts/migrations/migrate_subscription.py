import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text

def migrate():
    print("Iniciando migracao de assinatura...")
    with engine.connect() as conn:
        # Check if columns exist (SQLite doesn't support 'IF NOT EXISTS' in ALTER TABLE nicely for columns, so we try/except or inspect)
        # We will just try to add them and catch errors if they exist, or check prone logic.
        # SQLite simple approach:
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN subscription_end_date DATETIME"))
            print("- Coluna 'subscription_end_date' adicionada.")
        except Exception as e:
            print(f"- Coluna 'subscription_end_date' provavelment ja existe: {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN subscription_status VARCHAR DEFAULT 'inactive'"))
            print("- Coluna 'subscription_status' adicionada.")
        except Exception as e:
            print(f"- Coluna 'subscription_status' provavelment ja existe: {e}")

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN subscription_plan VARCHAR DEFAULT 'free'"))
            print("- Coluna 'subscription_plan' adicionada.")
        except Exception as e:
            print(f"- Coluna 'subscription_plan' provavelment ja existe: {e}")

        conn.commit()
    print("Migracao concluida.")

if __name__ == "__main__":
    migrate()
