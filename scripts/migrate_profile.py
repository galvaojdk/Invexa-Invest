import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text

def migrate():
    print("Iniciando migracao de perfil...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR"))
            print("- Coluna 'phone_number' adicionada.")
        except Exception as e:
            print(f"- Coluna 'phone_number' provavelment ja existe: {e}")

        conn.commit()
    print("Migracao concluida.")

if __name__ == "__main__":
    migrate()
