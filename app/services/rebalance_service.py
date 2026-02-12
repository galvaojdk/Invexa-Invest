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

        # 4. Filter relevant targets (categories)
        category_targets = [t for t in targets if t.target_type == 'category']
        new_total_equity = total_equity + contribution_amount
        
        valid_allocations = [] # Stores (target, candidates, weight)
        total_weight = 0.0
        
        # 5. Pass 1: Identificar gaps e buscar candidatos válidos
        for target in category_targets:
            target_name = target.name.lower() # 'stock', 'fii'
            target_val = new_total_equity * (target.target_percent / 100.0)
            current_val = current_alloc.get(target_name, 0.0)
            
            # Gap based on deficit
            raw_gap = target_val - current_val
            
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
            
            # Filter out 'Caro' assets
            # A menos que não haja nenhuma outra opção? Por enquanto somos rigorosos.
            candidates = [c for c in candidates if c['status'] != 'Caro']
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            if candidates:
                valid_allocations.append({
                    "target": target,
                    "candidates": candidates,
                    "raw_gap": raw_gap,
                    # Inicialmente peso é o gap positivo. Se for negativo/zero, peso 0.
                    "weight": max(0, raw_gap)
                })

        # 6. Recalcular Pesos (Redistribuição)
        # Calcula soma dos pesos (gaps positivos)
        total_weight = sum(item['weight'] for item in valid_allocations)
        
        # Se total_weight for 0 (nenhum gap positivo ou carteira balanceada), 
        # mas temos candidatos válidos, usamos o Target % para distribuir o aporte.
        if total_weight == 0 and valid_allocations:
             total_weight = sum(item['target'].target_percent for item in valid_allocations)
             for item in valid_allocations:
                 item['weight'] = item['target'].target_percent
        
        # Se ainda sim total_weight for 0 (ex: tudo caro), não sugerimos nada.
        
        suggestions = []

        # 7. Pass 2: Distribuir o Aporte
        if total_weight > 0:
            for item in valid_allocations:
                if item['weight'] <= 0: continue
                
                # Alocação Proporcional do Aporte disponível
                allocation_amt = contribution_amount * (item['weight'] / total_weight)
                
                if allocation_amt < 1: continue 

                # Pulverização
                top_candidates = item['candidates'][:3]
                amount_per_asset = allocation_amt / len(top_candidates)
                
                for cand in top_candidates:
                    asset = cand['asset']
                    if not asset.price or asset.price == 0: continue
                    
                    # Tentar garantir compra mínima
                    if amount_per_asset < asset.price:
                         if allocation_amt >= asset.price:
                             amount_per_asset = allocation_amt
                    
                    shares = int(amount_per_asset / asset.price)
                    if shares > 0:
                         reason = ""
                         if cand['owned']:
                             reason = f"Aumentar posição em {item['target'].name.upper()} ({cand['status']})"
                         else:
                             reason = f"Oportunidade em {item['target'].name.upper()} ({cand['status']})"
                             
                         suggestions.append({
                            "ticker": asset.ticker,
                            "category": item['target'].name.upper(),
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
            
    # Keep singleton
rebalance_service = RebalanceService()
