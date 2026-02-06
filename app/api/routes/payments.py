from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.dashboard import get_current_active_user as get_current_user
from app.models.user import User
import mercadopago
import os
import logging

# Configure Logging
logger = logging.getLogger(__name__)

router = APIRouter()

# HARDCODED ACCESS TOKEN FOR DEMO (Replace with env var in production)
# TEST-7239335607378850-020516-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-166887532
# Using a dummy format for safety if not present
from app.models.setting import Setting

# Remove Global SDK init to allow dynamic token
# sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

@router.post("/checkout")
async def create_checkout_preference(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a Mercado Pago preference and returns the init_point (checkout URL).
    """
    
    # Check if user is already premium
    if current_user.is_premium:
        return {"message": "User is already premium", "redirect": "/dashboard"}

    import json
    
    # 1. Try to fetch Multi-Credential List
    settings_creds = db.query(Setting).filter(Setting.key == "MP_CREDENTIALS").first()
    active_token = None
    
    if settings_creds and settings_creds.value:
        try:
            creds_list = json.loads(settings_creds.value)
            # Find the active one
            for cred in creds_list:
                if cred.get('active'):
                    active_token = cred.get('token')
                    break
        except Exception as e:
            logger.error(f"Error parsing MP_CREDENTIALS: {e}")

    # 2. Fallback to single token (Legacy)
    if not active_token:
        settings_token = db.query(Setting).filter(Setting.key == "MP_ACCESS_TOKEN").first()
        if settings_token and settings_token.value:
            active_token = settings_token.value

    # 3. Final Check
    if not active_token:
        logger.error("No active Mercado Pago token found.")
        raise HTTPException(status_code=500, detail="Configuração de Pagamento não encontrada. Verifique o Painel Admin.")
        
    # Init SDK dynamically
    sdk = mercadopago.SDK(active_token)

    # Receive Plan Type from frontend (default monthly)
    body_data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    plan_type = body_data.get('plan_type', 'monthly')
    
    # Calculate Price and Title
    if plan_type == 'annual':
        price = 322.90 # (29.90 * 12) * 0.9 = 322.92 -> rounding to nice number
        title = "Invexa Premium (Anual)"
        months_duration = 12
    else:
        price = 29.90
        title = "Invexa Premium (Mensal)"
        months_duration = 1

    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": float(price),
                "currency_id": "BRL"
            }
        ],
        "payer": {
            "email": current_user.email,
            "name": current_user.full_name or "Usuario Invexa"
        },
        "external_reference": f"{current_user.id}|{plan_type}", # Pass plan type in ref
        "back_urls": {
            "success": "http://localhost:8000/dashboard?status=premium_success",
            "failure": "http://localhost:8000/dashboard?status=premium_failure",
            "pending": "http://localhost:8000/dashboard?status=premium_pending"
        }
        # "auto_return": "approved" # Disable auto_return for localhost development
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response["status"] not in [200, 201]:
             error_detail = preference_response["response"]
             logger.error(f"MP Create Preference Failed: {error_detail}")
             raise HTTPException(status_code=500, detail=f"Erro Mercado Pago: {error_detail.get('message', 'Unknown Error')}")

        result = preference_response["response"]
        
        # sandbox_init_point for testing, init_point for production
        checkout_url = result.get("sandbox_init_point") if result.get("sandbox_init_point") else result.get("init_point") 
        
        if not checkout_url:
             raise HTTPException(status_code=500, detail="Checkout URL not returned by MP")

        return {"checkout_url": checkout_url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating MP preference: {e}")
        raise HTTPException(status_code=500, detail=f"Erro Interno: {str(e)}")

@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receives notifications from Mercado Pago
    """
    try:
        # 1. Parse content
        params = request.query_params
        body = await request.json()
        
        topic = params.get("topic") or body.get("type")
        payment_id = params.get("id") or body.get("data", {}).get("id")

        logger.info(f"Webhook received: topic={topic}, payment_id={payment_id}")

        if topic == "payment" and payment_id:
            # Fetch Token Again for Webhook
            import json
            settings_creds = db.query(Setting).filter(Setting.key == "MP_CREDENTIALS").first()
            active_token = None
            
            if settings_creds and settings_creds.value:
                try:
                    creds_list = json.loads(settings_creds.value)
                    for cred in creds_list:
                        if cred.get('active'):
                            active_token = cred.get('token')
                            break
                except: pass
            
            if not active_token:
                 settings_token = db.query(Setting).filter(Setting.key == "MP_ACCESS_TOKEN").first()
                 if settings_token: active_token = settings_token.value
            
            if not active_token:
                 logger.error("Webhook Error: MP Token not found in settings")
                 return {"status": "error", "detail": "Missing Configuration"}
            
            sdk = mercadopago.SDK(active_token)

            # 2. Verify payment status with MP API
            payment_info = sdk.payment().get(payment_id)
            payment_data = payment_info["response"]
            
            status_detail = payment_data.get("status")
            external_ref = payment_data.get("external_reference")
            
            logger.info(f"Payment {payment_id} status: {status_detail} for Ref: {external_ref}")

            if status_detail == "approved" and external_ref:
                # 3. Grant Premium Access
                # Parse Ref: "user_id|plan_type"
                parts = external_ref.split('|')
                user_id = int(parts[0])
                plan_type = parts[1] if len(parts) > 1 else 'monthly'
                
                user = db.query(User).filter(User.id == user_id).first()
                
                if user:
                    from datetime import datetime, timedelta
                    
                    user.is_premium = True
                    user.subscription_plan = plan_type
                    user.subscription_status = 'active'
                    
                    # Calculate new end date
                    now = datetime.now()
                    current_end = user.subscription_end_date
                    
                    # If already active and not expired, extend. Else start from now.
                    start_date = now
                    if current_end and current_end > now:
                        start_date = current_end
                    
                    duration_days = 365 if plan_type == 'annual' else 30
                    user.subscription_end_date = start_date + timedelta(days=duration_days)
                    
                    db.commit()
                    logger.info(f"PREMIUM GRANTED for User ID {user_id} - Plan: {plan_type} - Until: {user.subscription_end_date}")
                    
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}
