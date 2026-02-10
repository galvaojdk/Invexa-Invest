from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core import database
from app.api.routes.dashboard import get_current_active_user
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services.news_service import news_service

router = APIRouter()

@router.get("")
@router.get("/")
async def get_personalized_news(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 1. Pegar tickers e nomes dos ativos do usuário
    portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    search_terms = []
    has_portfolio = len(portfolio_items) > 0
    
    for item in portfolio_items:
        if item.asset:
            search_terms.append(item.asset.ticker)
            if item.asset.name:
                # Pegar o primeiro nome (ex: Petrobras de "Petrobras SA")
                first_name = item.asset.name.split()[0]
                search_terms.append(first_name)
    
    # 2. Buscar notícias filtradas
    news = await news_service.get_news_for_portfolio(search_terms, has_portfolio=has_portfolio)
    
    return {
        "user_tickers": [item.asset.ticker for item in portfolio_items if item.asset],
        "news": news
    }
