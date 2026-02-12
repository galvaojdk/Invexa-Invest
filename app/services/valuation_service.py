from app.models.asset import Asset
from typing import Dict, Any, Tuple

class ValuationService:
    @staticmethod
    def calculate_fair_price(asset: Asset) -> Tuple[float, str]:
        """
        Calculates fair price based on asset type:
        - Stocks: Graham Formula (Sqrt(22.5 * LPA * VPA))
        - FIIs/Dividend Stocks: Bazin (DY / 6%)
        
        Returns: (fair_price, status)
        Status: "Descontado", "Neutro", "Caro"
        """
        if not asset.price or asset.price <= 0:
            return 0.0, "Neutro"

        fair_price = 0.0
        status = "Neutro"
        
        # 1. Graham (Classic for Stocks)
        if asset.type == 'stock':
            # Only valid if LPA and VPA are positive
            if asset.lpa > 0 and asset.vpa > 0:
                try:
                    fair_price = (22.5 * asset.lpa * asset.vpa) ** 0.5
                except:
                    fair_price = 0.0
            
            # If Graham fails or is 0, maybe fallback to Bazin if it pays dividends?
            # For now, strict Graham for stocks as requested, unless it's a dividend stock
            # but we treat 'stock' as general.
            
            if fair_price > 0:
                if asset.price < fair_price:
                    status = "Descontado"
                elif asset.price > fair_price * 1.1: # 10% margin
                    status = "Caro"
                else:
                    status = "Neutro"
            else:
                 # Fallback logic if Graham is invalid (e.g. loss making)
                 if asset.dy_12m and asset.dy_12m > 6:
                     # Calculate max price for 6% yield
                     fair_price = (asset.price * (asset.dy_12m / 100)) / 0.06
                     if asset.price < fair_price:
                         status = "Bom Pagador"
                 
                 # Fallback 2: P/VP for Stocks (if Graham and Div failed)
                 if status == "Neutro" and asset.p_vp > 0:
                     if asset.p_vp < 1.0:
                         # Assume fair price is P/VP = 1.0
                         fair_price_pvp = asset.price / asset.p_vp
                         status = "Descontado"
                         if fair_price == 0: fair_price = fair_price_pvp
                     elif asset.p_vp > 1.5: # Margin for expensive
                          status = "Caro"
        
        # 2. Bazin (For FIIs or High Dividend Stocks)
        # We prioritize Bazin for FIIs
        if asset.type == 'fii':
             if asset.dy_12m and asset.dy_12m > 0:
                 # Annual payment estimate
                 dividend_val = (asset.price * (asset.dy_12m / 100))
                 fair_price_bazin = dividend_val / 0.06
                 
                 fair_price = fair_price_bazin
                 
                 if asset.price < fair_price:
                     status = "Descontado"
                 elif asset.price > fair_price * 1.05:
                     status = "Caro"
                 else:
                     status = "Neutro"
             else:
                 # Fallback to P/VP for FIIs if no dividend info
                 if asset.p_vp > 0:
                     if asset.p_vp < 0.90:
                         status = "Descontado"
                         fair_price = asset.price / asset.p_vp # Target P/VP = 1
                     elif asset.p_vp > 1.10:
                         status = "Caro"
                         fair_price = asset.price / asset.p_vp
        
        return fair_price, status

valuation_service = ValuationService()
