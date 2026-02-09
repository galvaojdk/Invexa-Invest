from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Invexa"
    API_V1_STR: str = "/api/v1"
    
    # Segurança
    SECRET_KEY: str = "supersecretkey_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Banco de Dados
    # SQLite por padrão para facilidade no MVP
    # Ler do Render (DATABASE_URL) ou usar SQLite local
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./invexa.db"

    def __init__(self, **kwargs):
        import os
        super().__init__(**kwargs)
        
        # 1. Se existir DATABASE_URL (Render), priorizar ela
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            self.SQLALCHEMY_DATABASE_URI = database_url
            
        # 2. Corrigir protocolo do Render (postgres:// -> postgresql://)
        # SQLAlchemy requer postgresql://
        if self.SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            self.SQLALCHEMY_DATABASE_URI = self.SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
