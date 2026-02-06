from fastapi import FastAPI, Request
import os
import time
# Invexa Main Application
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core import config, database
from app.models import user, asset, portfolio
from app.api.routes import auth, views, dashboard, assets, portfolio as portfolio_routes, admin, premium, payments, profile

# Criação de tabelas movida para o evento de startup para evitar erros de importação
# se o banco ainda não estiver acessível.

app = FastAPI(title=config.settings.PROJECT_NAME)

app.mount("/static", StaticFiles(directory="app/static"), name="static") if os.path.exists("app/static") else print("WARN: static directory not found, skipping mount")
templates = Jinja2Templates(directory="app/templates")

# Incluir Routers
app.include_router(auth.router, prefix=config.settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(dashboard.router, prefix=config.settings.API_V1_STR + "/dashboard", tags=["dashboard"])
app.include_router(assets.router, prefix=config.settings.API_V1_STR + "/assets", tags=["assets"])
app.include_router(portfolio_routes.router, prefix=config.settings.API_V1_STR + "/portfolio", tags=["portfolio"])
app.include_router(admin.router, prefix=config.settings.API_V1_STR + "/admin", tags=["admin"])
app.include_router(premium.router, prefix=config.settings.API_V1_STR + "/premium", tags=["premium"])
app.include_router(payments.router, prefix=config.settings.API_V1_STR + "/payments", tags=["payments"])
app.include_router(profile.router, prefix=config.settings.API_V1_STR + "/profile", tags=["profile"])
app.include_router(views.router, tags=["views"])

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    # Cria tabelas no banco de dados (para MVP)
    # Isso garante que a tentativa de conexão ocorra apenas quando o app estiver rodando
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Debug: Imprimir URL mascarada para verificar o host
            from app.core import config
            db_url = config.settings.SQLALCHEMY_DATABASE_URI
            if "@" in db_url:
                # Mascarar senha: postgresql://user:pass@host:port/db -> postgresql://user:***@host:port/db
                part1, part2 = db_url.split("@", 1)
                protocol_user = part1.split(":")[0] 
                print(f"DEBUG: Connecting to DB Host: {part2.split('/')[0]}")
                print(f"DEBUG: Full URL (Masked): {part1.split(':')[0]}:***@{part2}")
            
            from app.models.alert import Alert
            from app.models.setting import Setting
            print(f"Connecting to database (Attempt {attempt + 1}/{max_retries})...")
            user.Base.metadata.create_all(bind=database.engine)
            asset.Base.metadata.create_all(bind=database.engine)
            portfolio.Base.metadata.create_all(bind=database.engine)
            Alert.metadata.create_all(bind=database.engine)
            Setting.metadata.create_all(bind=database.engine)
            print("TABLES CREATED SUCCESSFULLY")
            break
        except Exception as e:
            print(f"ERROR CREATING TABLES (Attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print("Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print("FAILED TO CONNECT TO DATABASE AFTER MULTIPLE ATTEMPTS.")

    print("\n" + "="*50)
    print("SERVER STARTED - CHECKING ROUTES")
    print("="*50)
    with open("routes_dump.txt", "w") as f:
        f.write("--- ROUTES REGISTERED ---\n")
        for route in app.routes:
            if hasattr(route, "path"):
                msg = f"{route.path} -> {route.name}\n"
                f.write(msg)
                if "profile" in route.path:
                    print(f"ROUTE REGISTERED: {route.path} -> {route.name}")
    print("="*50 + "\n")

@app.get("/health")
def health_check():
    return {"status": "ok"}
