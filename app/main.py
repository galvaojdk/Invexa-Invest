from fastapi import FastAPI, Request
# Invexa Main Application
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core import config, database
from app.models import user, asset, portfolio
from app.api.routes import auth, views, dashboard, assets, portfolio as portfolio_routes, admin, premium, payments, profile

# Cria tabelas no banco de dados (para MVP - em prod usar Alembic)
user.Base.metadata.create_all(bind=database.engine)
asset.Base.metadata.create_all(bind=database.engine)
portfolio.Base.metadata.create_all(bind=database.engine)
from app.models.alert import Alert
from app.models.setting import Setting
Alert.metadata.create_all(bind=database.engine)
Setting.metadata.create_all(bind=database.engine)

app = FastAPI(title=config.settings.PROJECT_NAME)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
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
