from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core import database, security
from app.models.user import User
from app.api.routes.dashboard import get_current_active_user
from fastapi.templating import Jinja2Templates
from fastapi import File, UploadFile
import os
import uuid
import shutil

router = APIRouter()

# --- Schemas ---
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class PasswordUpdate(BaseModel):
    password: str

# --- Routes ---

@router.get("/data")
def get_profile_data(current_user: User = Depends(get_current_active_user)):
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "is_premium": current_user.is_premium,
        "subscription_plan": current_user.subscription_plan,
        "profile_pic": current_user.profile_pic,
        "subscription_end_date": current_user.subscription_end_date.strftime('%d/%m/%Y') if current_user.subscription_end_date else None
    }

@router.post("/update")
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.phone_number is not None:
        current_user.phone_number = data.phone_number
        
    db.commit()
    return {"status": "success", "message": "Perfil atualizado"}

@router.post("/security")
def update_password(
    data: PasswordUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
):
    if len(data.password) < 4:
        raise HTTPException(status_code=400, detail="Senha muito curta")
        
    hashed_password = security.get_password_hash(data.password)
    current_user.hashed_password = hashed_password
    db.commit()
    
    return {"status": "success", "message": "Senha alterada"}

@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Validar tipo de arquivo
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
    
    # Criar diretório se não existir
    upload_dir = "app/static/uploads/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Gerar nome único
    extension = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    filepath = os.path.join(upload_dir, filename)
    
    # Salvar arquivo
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Atualizar usuário
    current_user.profile_pic = f"/static/uploads/avatars/{filename}"
    db.commit()
    
    return {"status": "success", "url": current_user.profile_pic}
