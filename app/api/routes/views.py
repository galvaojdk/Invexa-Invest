from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def dashboard_view(request: Request):
    # Em uma app real, checaria o token JWT nos cookies ou header aqui
    # E buscaria dados reais do banco
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_name": "Investidor"
    })

@router.get("/screener")
async def screener_view(request: Request):
    return templates.TemplateResponse("screener.html", {
        "request": request,
        "free_limit": 1
    })

@router.get("/portfolio", response_class=HTMLResponse)
def portfolio(request: Request):
    return templates.TemplateResponse("portfolio.html", {"request": request})

@router.get("/portfolio/targets", response_class=HTMLResponse)
def portfolio_targets(request: Request):
    return templates.TemplateResponse("targets.html", {"request": request})

@router.get("/rankings/fiis", response_class=HTMLResponse)
def ranking_fiis(request: Request):
    return templates.TemplateResponse("screener.html", {"request": request, "asset_type": "fii", "page_title": "Ranking de FIIs", "free_limit": 3})

@router.get("/rankings/acoes", response_class=HTMLResponse)
def ranking_acoes(request: Request):
    return templates.TemplateResponse("screener.html", {"request": request, "asset_type": "stock", "page_title": "Ranking de Ações", "free_limit": 3})

@router.get("/ferramentas/juros", response_class=HTMLResponse)
def tools_juros(request: Request):
    return templates.TemplateResponse("calculator.html", {"request": request})

@router.get("/ferramentas/fire", response_class=HTMLResponse)
def tools_fire(request: Request):
    return templates.TemplateResponse("retirement.html", {"request": request})

@router.get("/ferramentas/comparador", response_class=HTMLResponse)
def tools_comparator(request: Request):
    return templates.TemplateResponse("tools/comparator.html", {"request": request})

@router.get("/ferramentas/valuation", response_class=HTMLResponse)
def tools_valuation(request: Request):
    return templates.TemplateResponse("tools/valuation.html", {"request": request})

@router.get("/ferramentas/agenda", response_class=HTMLResponse)
def tools_calendar(request: Request):
    return templates.TemplateResponse("tools/calendar.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
def profile_view(request: Request):
    # Renderizamos o template vazio/básico e o JS busca os dados
    return templates.TemplateResponse("profile.html", {"request": request, "user": None})



@router.get("/premium/subscribe", response_class=HTMLResponse)
async def premium_subscribe(request: Request):
    return templates.TemplateResponse("premium_sub.html", {"request": request})

@router.get("/login")
async def login_view(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request
    })

@router.get("/register")
async def register_view(request: Request):
    return templates.TemplateResponse("register.html", {
        "request": request
    })

@router.get("/logout")
async def logout_view(request: Request):
    # Simples redirect para login por enquanto
    # Idealmente limparia cookies de sessão
    return templates.TemplateResponse("login.html", {"request": request})
