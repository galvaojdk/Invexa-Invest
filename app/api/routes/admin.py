from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core import database
from app.models.user import User
from app.models.portfolio import Portfolio
from app.schemas import UserResponse
from app.api.routes.dashboard import get_current_admin_user

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(database.get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    users = db.query(User).all()
    return users

@router.post("/users/{user_id}/toggle-premium")
def toggle_premium_status(
    user_id: int,
    duration_days: int = 30,
    db: Session = Depends(database.get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Toggle (If sending specific duration, assume we want to turn ON or extend)
    # But to keep simple compatible logic:
    # If currently Free -> Make Premium with duration
    # If currently Premium -> Make Free (toggle off) OR Extend?
    # Let's assume Toggle behavior:
    
    if user.is_premium:
        # Turn OFF
        user.is_premium = False
        user.subscription_status = "inactive"
        user.subscription_end_date = None
        user.subscription_plan = "free"
    else:
        # Turn ON
        user.is_premium = True
        from datetime import datetime, timedelta
        user.subscription_status = "active"
        user.subscription_plan = "manual_admin"
        user.subscription_end_date = datetime.now() + timedelta(days=duration_days)
    
    db.commit()
    db.refresh(user)
    
    status_text = "Premium" if user.is_premium else "Free"
    return {"message": f"Status do usuário alterado para {status_text}", "is_premium": user.is_premium}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir a si mesmo.")
    
    # Delete dependent data (Portfolio)
    db.query(Portfolio).filter(Portfolio.user_id == user_id).delete()
    
    db.delete(user)
    db.commit()
    
    return {"message": "Usuário excluído com sucesso"}
from app.models.setting import Setting
from pydantic import BaseModel

class SettingUpdate(BaseModel):
    key: str
    value: str

@router.get("/settings")
def get_settings(
    db: Session = Depends(database.get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    settings = db.query(Setting).all()
    # Convert list to dict for easier frontend consumption
    return {s.key: s.value for s in settings}

@router.post("/settings")
def update_setting(
    setting: SettingUpdate,
    db: Session = Depends(database.get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    db_setting = db.query(Setting).filter(Setting.key == setting.key).first()
    if db_setting:
        db_setting.value = setting.value
    else:
        db_setting = Setting(key=setting.key, value=setting.value)
        db.add(db_setting)
    
    db.commit()
    return {"message": "Configuração atualizada com sucesso"}
