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
        if self.SQLALCHEMY_DATABASE_URI and self.SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            self.SQLALCHEMY_DATABASE_URI = self.SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

        # 3. Fix para Render Internal URL (às vezes vem sem o FQDN)
        # Ex: postgresql://user:pass@dpg-xxxx-a:5432/db
        # Deve ser: postgresql://user:pass@dpg-xxxx-a.ohio-postgres.render.com:5432/db
        if "dpg-" in self.SQLALCHEMY_DATABASE_URI and ".render.com" not in self.SQLALCHEMY_DATABASE_URI and "postgresql://" in self.SQLALCHEMY_DATABASE_URI:
            try:
                # Separar partes da URL
                part1, part2 = self.SQLALCHEMY_DATABASE_URI.split("@", 1) # user:pass @ host:port/db
                host_part = part2.split("/")[0] # host:port
                
                if ":" in host_part:
                    host_only = host_part.split(":")[0] # host
                    if "dpg-" in host_only and "." not in host_only:
                        # Rebuild URL
                        new_host = f"{host_only}.ohio-postgres.render.com"
                        self.SQLALCHEMY_DATABASE_URI = self.SQLALCHEMY_DATABASE_URI.replace(host_only, new_host, 1)
                        print(f"WARN: Fixed Render Hostname: {host_only} -> {new_host}")
            except Exception as e:
                print(f"WARN: Failed to fix Render URL: {e}")

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
