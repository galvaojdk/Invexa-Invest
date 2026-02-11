from sqlalchemy.orm import Session
from app.models.portfolio import Portfolio
from app.models.asset import Asset
from app.models.user_target import UserTarget
from typing import List, Dict, Any

class RebalanceService:
    @staticmethod
    def get_rebalance_suggestions(db: Session, user_id: int, contribution_amount: float) -> List[Dict[str, Any]]:
        # 1. Get current portfolio
        portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user_id, Portfolio.quantity > 0).all()
        
        if not portfolio_items:
            return []

        # 2. Get user targets
        targets = db.query(UserTarget).filter(UserTarget.user_id == user_id).all()
        if not targets:
            # If no targets, we can't really suggest anything specific beyond "buy what you have" 
            # or maybe just return empty to prompt user to set targets.
            return []

        # 3. Calculate current total equity and breakdown by category/asset
        total_equity = 0.0
        current_alloc = {} # Key: target name (e.g. 'stock', 'fii'), Value: total current value
        
        # We need to link portfolio assets to targets
        # For simplicity in this first version, we'll support category targets ('stock', 'fii')
        for item in portfolio_items:
            asset = item.asset
            if not asset: continue
            
            value = item.quantity * (asset.price or 0.0)
            total_equity += value
            
            asset_type = asset.type # 'stock' or 'fii'
            current_alloc[asset_type] = current_alloc.get(asset_type, 0.0) + value

        # 4. Filter relevant targets (categories for now)
        category_targets = [t for t in targets if t.target_type == 'category']
        
        # 5. Determine how to distribute the new contribution
        # We'll use a simple "fill the gap" approach
        new_total_equity = total_equity + contribution_amount
        
        suggestions = []
        
        # Calculate how much SHOULD be in each category
        for target in category_targets:
            target_value = new_total_equity * (target.target_percent / 100.0)
            current_value = current_alloc.get(target.name, 0.0)
            
            gap = target_value - current_value
            if gap > 0:
                # We should invest 'gap' amount in this category
                # Now, which asset within this category?
                # Simple rule: pick the asset within this category that is also below its "inner" target 
                # or just pick the one with best DY/fundamental (for now let's just suggest the category)
                
                # To make it "Smart", let's suggest the top 1-2 assets in that category 
                # that have the lowest % of the wallet within that category.
                
                cat_assets = [item for item in portfolio_items if item.asset.type == target.name]
                if not cat_assets: continue
                
                # Suggest assets in this category
                # For a really smart suggestion, we could split the 'gap' among assets in the category
                # but let's keep it simple: distribute the gap among the cat_assets proportionally?
                # No, better to suggest buying the one that is most "lagging".
                
                # Sort cat_assets by current value (lower first)
                cat_assets.sort(key=lambda x: x.quantity * (x.asset.price or 0.0))
                
                # Let's suggest the top asset in this category
                best_asset = cat_assets[0].asset
                
                # Calculate how many shares of this asset to buy
                shares_to_buy = 0
                if best_asset.price and best_asset.price > 0:
                    shares_to_buy = int(gap / best_asset.price)
                
                if shares_to_buy > 0:
                    suggestions.append({
                        "ticker": best_asset.ticker,
                        "category": target.name,
                        "suggested_amount": gap,
                        "suggested_shares": shares_to_buy,
                        "current_price": best_asset.price,
                        "reason": f"Sua meta para {target.name.upper()} é {target.target_percent}%, mas atualmente está abaixo disso."
                    })

        # Sort suggestions by the magnitude of the gap (invest in most lagging first)
        suggestions.sort(key=lambda x: x['suggested_amount'], reverse=True)
        
        return suggestions

rebalance_service = RebalanceService()
