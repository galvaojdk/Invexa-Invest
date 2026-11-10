from sqlalchemy.orm import Session
from app.core import database
from app.models.setting import Setting
import json
import time

# Provide Token
NEW_TOKEN = "APP_USR-7802809046369492-020516-6a9abe3bde889389b0f1b569828188c4-3184584898"
LABEL = "Credencial de Teste (Corrigida)"

db = database.SessionLocal()

def inject_token():
    print(f"Injecting token: {NEW_TOKEN[:10]}...")
    
    # Get existing credentials
    setting = db.query(Setting).filter(Setting.key == "MP_CREDENTIALS").first()
    
    creds = []
    if setting and setting.value:
        try:
            creds = json.loads(setting.value)
        except:
             creds = []
             
    # Deactivate all existing
    for c in creds:
        c['active'] = False
        
    # Add new one
    new_cred = {
        "id": str(int(time.time()*1000)),
        "label": LABEL,
        "token": NEW_TOKEN,
        "active": True
    }
    creds.append(new_cred)
    
    json_val = json.dumps(creds)
    
    if setting:
        setting.value = json_val
    else:
        setting = Setting(key="MP_CREDENTIALS", value=json_val)
        db.add(setting)
        
    db.commit()
    print("Token injected successfully as ACTIVE.")

if __name__ == "__main__":
    inject_token()
