from sqlalchemy.orm import Session
from app.core import database
from app.models.setting import Setting
import json
import mercadopago

# Setup DB
db = database.SessionLocal()

def check_creds():
    print("--- Debugging MP Credentials ---")
    
    # 1. Check MP_CREDENTIALS
    settings_creds = db.query(Setting).filter(Setting.key == "MP_CREDENTIALS").first()
    
    if not settings_creds:
        print("MP_CREDENTIALS setting is MISSING.")
    else:
        print(f"Raw Value: {settings_creds.value}")
        try:
            creds_list = json.loads(settings_creds.value)
            print(f"Parsed JSON List ({len(creds_list)} items):")
            for i, c in enumerate(creds_list):
                print(f"  [{i}] Label: {c.get('label')}, Active: {c.get('active')}, Token: {c.get('token')[:10]}...")
            
            # Simulate Active Fetch
            active_token = None
            for cred in creds_list:
                if cred.get('active'):
                    active_token = cred.get('token')
                    break
            
            print(f"Active Token Logic Result: {active_token[:10] if active_token else 'None'}")
            
            if active_token:
                try:
                    sdk = mercadopago.SDK(active_token)
                    print("SDK Initialized. Attempting Preference Creation...")
                    
                    preference_data = {
                        "items": [
                            {"title": "Test Item Debug", "quantity": 1, "unit_price": 100.0, "currency_id": "BRL"}
                        ],
                        "payer": {
                            "email": "test_user_123@test.com"
                        }
                    }
                    result = sdk.preference().create(preference_data)
                    
                    if result["status"] == 201:
                         print(f"SUCCESS! Init Point: {result['response']['init_point']}")
                    else:
                         print(f"API ERROR: Status {result['status']}")
                         print(f"Response: {result['response']}")
                         
                except Exception as e:
                    print(f"SDK Exception: {e}")

        except Exception as e:
             print(f"JSON Parse Error: {e}")

    # 2. Check Fallback
    settings_token = db.query(Setting).filter(Setting.key == "MP_ACCESS_TOKEN").first()
    if settings_token:
        print(f"Fallback MP_ACCESS_TOKEN value: {settings_token.value[:10] if settings_token.value else 'None'}...")
    else:
        print("Fallback MP_ACCESS_TOKEN setting is MISSING.")

if __name__ == "__main__":
    check_creds()
