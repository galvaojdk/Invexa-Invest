from sqlalchemy.orm import Session
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.user_target import UserTarget
from app.services.valuation_service import valuation_service
from typing import List, Dict, Any

class RebalanceService:
    @staticmethod
    def get_rebalance_suggestions(db: Session, user_id: int, contribution_amount: float) -> List[Dict[str, Any]]:
        # 1. Get current portfolio
        portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user_id, Portfolio.quantity > 0).all()
        
        # 2. Get user targets
        targets = db.query(UserTarget).filter(UserTarget.user_id == user_id).all()
        if not targets:
            return []

        # 3. Calculate current total equity and breakdown
        total_equity = 0.0
        current_alloc = {}
        owned_asset_ids = set()
        
        for item in portfolio_items:
            asset = item.asset
            if not asset: continue
            
            value = item.quantity * (asset.price or 0.0)
            total_equity += value
            
            asset_type = asset.type.lower() if asset.type else 'outros'
            current_alloc[asset_type] = current_alloc.get(asset_type, 0.0) + value
            owned_asset_ids.add(asset.id)

        # 4. Determine Target Amounts
        category_targets = [t for t in targets if t.target_type == 'category']
        new_total_equity = total_equity + contribution_amount
        
        suggestions = []
        
        # 5. Process each category
        for target in category_targets:
            target_name = target.name.lower() # 'stock', 'fii'
            target_val = new_total_equity * (target.target_percent / 100.0)
            current_val = current_alloc.get(target_name, 0.0)
            
            gap = target_val - current_val
            
            if gap > 0:
                # We need to invest 'gap' into this category.
                # Find candidates: 
                # A) Owned assets in this category
                # B) Top discounted assets in DB for this category
                
                candidates = []
                
                # A. Owned
                owned_in_cat = [item.asset for item in portfolio_items if item.asset.type == target_name]
                for asset in owned_in_cat:
                    fp, status = valuation_service.calculate_fair_price(asset)
                    candidates.append({
                        "asset": asset,
                        "status": status,
                        "fair_price": fp,
                        "owned": True,
                        "score": RebalanceService._score_asset(asset, status, True)
                    })
                
                # B. New Opportunities (Limit to avoid performance hit)
                # Fetch top 20 by liquidity/dy to filter
                # Ideally we'd have a 'ranking' table, but let's query raw for now
                if target_name in ['stock', 'fii']:
                     potential_new = db.query(Asset).filter(
                         Asset.type == target_name,
                         Asset.id.notin_(owned_asset_ids),
                         Asset.price > 0
                     ).order_by(Asset.liquidity_avg_2m.desc()).limit(20).all()
                     
                     for asset in potential_new:
                         fp, status = valuation_service.calculate_fair_price(asset)
                         # Only suggest if Descontado or Bom Pagador
                         if status in ["Descontado", "Bom Pagador"]:
                             candidates.append({
                                 "asset": asset,
                                 "status": status,
                                 "fair_price": fp,
                                 "owned": False,
                                 "score": RebalanceService._score_asset(asset, status, False)
                             })
                
                # Sort candidates by score
                candidates.sort(key=lambda x: x['score'], reverse=True)
                
                # Filter out 'Caro' assets to protect user, unless we have no other choice?
                # Let's be strict: Don't suggest buying 'Caro'.
                candidates = [c for c in candidates if c['status'] != 'Caro']
                
                # Pulverization Logic
                # Pick top 3 candidates to spread the 'gap'
                top_candidates = candidates[:3]
                
                if not top_candidates: continue
                
                # Distribute gap evenly (simplified) or weighted?
                # Let's do evenly for now to "pulverize"
                amount_per_asset = gap / len(top_candidates)
                
                for cand in top_candidates:
                    asset = cand['asset']
                    if not asset.price or asset.price == 0: continue
                    
                    # Check if amount is enough for at least 1 share
                    if amount_per_asset < asset.price:
                        # Try to buy at least 1 if possible with total gap?
                        # If gap is small, maybe just 1 asset gets it.
                        if gap >= asset.price:
                             amount_per_asset = gap # Dump all in best for this iteration
                    
                    shares = int(amount_per_asset / asset.price)
                    if shares > 0:
                         reason = ""
                         if cand['owned']:
                             reason = f"Aumentar posição em {target.name.upper()} ({cand['status']})"
                         else:
                             reason = f"Oportunidade em {target.name.upper()} ({cand['status']})"
                             
                         suggestions.append({
                            "ticker": asset.ticker,
                            "category": target.name.upper(),
                            "suggested_amount": shares * asset.price,
                            "suggested_shares": shares,
                            "current_price": asset.price,
                            "reason": reason,
                            "status": cand['status']
                         })

        # Sort final suggestions by amount
        suggestions.sort(key=lambda x: x['suggested_amount'], reverse=True)
        return suggestions

    @staticmethod
    def _score_asset(asset: Asset, status: str, owned: bool) -> float:
        # Simple scoring system
        score = 0.0
        
        # Valuation (High weight)
        if status == "Descontado": score += 50
        elif status == "Bom Pagador": score += 30
        elif status == "Neutro": score += 10
        elif status == "Caro": score -= 20
        
        # Preference to owned assets (to avoid infinite scattering, unless new is really good)
        if owned: score += 15
        
        # Quality/Liquidity Bonus (Tiny to break ties)
        if asset.liquidity_avg_2m > 1_000_000: score += 5
        
        # Dividends Bonus
        if asset.dy_12m > 6: score += (asset.dy_12m) # +6 to +15 pts
        
        return score

rebalance_service = RebalanceService()
