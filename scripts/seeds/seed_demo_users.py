import sys
import os
from datetime import datetime, timedelta

# Adiciona a raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import app.models
from app.core import database, security
from app.models.user import User

def seed_demo_users():
    db = database.SessionLocal()
    try:
        # Usuário Comum / Premium Demo
        user_demo = db.query(User).filter(User.email == "demo@invexa.com").first()
        if not user_demo:
            user_demo = User(
                email="demo@invexa.com",
                hashed_password=security.get_password_hash("demo123"),
                full_name="Investidor Demo",
                is_active=True,
                is_admin=False,
                is_premium=True,
                role="user",
                subscription_status="active",
                subscription_plan="annual",
                subscription_end_date=datetime.now() + timedelta(days=365)
            )
            db.add(user_demo)
            print("[+] Criado usuario demo: demo@invexa.com / demo123")
        else:
            user_demo.hashed_password = security.get_password_hash("demo123")
            user_demo.is_premium = True
            print("[*] Atualizado usuario demo: demo@invexa.com / demo123")

        # Administrador Demo
        admin_user = db.query(User).filter(User.email == "admin@invexa.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@invexa.com",
                hashed_password=security.get_password_hash("admin123"),
                full_name="Administrador Invexa",
                is_active=True,
                is_admin=True,
                is_premium=True,
                role="admin",
                subscription_status="active",
                subscription_plan="annual",
                subscription_end_date=datetime.now() + timedelta(days=365)
            )
            db.add(admin_user)
            print("[+] Criado usuario admin: admin@invexa.com / admin123")
        else:
            admin_user.hashed_password = security.get_password_hash("admin123")
            admin_user.is_admin = True
            print("[*] Atualizado usuario admin: admin@invexa.com / admin123")

        db.commit()
        print("[OK] Usuarios demo prontos no banco de dados!")
    except Exception as e:
        db.rollback()
        print(f"[ERRO] Falha ao criar usuarios demo: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_users()

