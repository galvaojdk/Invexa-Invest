from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings

def migrate():
    print(f"Iniciando migração no banco: {settings.SQLALCHEMY_DATABASE_URI.split('@')[-1]}")
    
    with engine.connect() as conn:
        try:
            # Tentar adicionar a coluna profile_pic
            # No PostgreSQL, usamos ALTER TABLE
            print("Tentando adicionar coluna 'profile_pic' à tabela 'users'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_pic TEXT"))
            conn.commit()
            print("Sucesso! Coluna 'profile_pic' verificada/adicionada.")
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            print("Nota: Se o erro for 'column already exists', você pode ignorar.")

if __name__ == "__main__":
    migrate()
