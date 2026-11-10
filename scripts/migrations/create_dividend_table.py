from app.core.database import SessionLocal, engine, Base
from app.models.dividend import DividendEvent
from app.models.asset import Asset
from sqlalchemy import text

def create_table():
    print("Criando tabela 'dividend_events'...")
    DividendEvent.__table__.create(bind=engine, checkfirst=True)
    print("Tabela criada com sucesso.")

if __name__ == "__main__":
    create_table()
