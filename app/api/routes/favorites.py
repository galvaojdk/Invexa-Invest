from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.dashboard import get_current_active_user
from app.models.user import User
from app.models.asset import Asset
from app.schemas import AssetResponse
from typing import List

router = APIRouter()

@router.post("/toggle/{ticker}")
def toggle_favorite(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    
    if asset in current_user.favorites:
        current_user.favorites.remove(asset)
        added = False
    else:
        current_user.favorites.append(asset)
        added = True
    
    db.commit()
    return {"message": "Favoritos atualizado", "added": added, "ticker": asset.ticker}

@router.get("/", response_model=List[AssetResponse])
def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return current_user.favorites
