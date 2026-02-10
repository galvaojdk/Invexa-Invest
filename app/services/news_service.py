import feedparser
import httpx
import asyncio
from typing import List, Dict
from datetime import datetime
import time

class NewsService:
    def __init__(self):
        self.sources = [
            "https://br.investing.com/rss/news_25.rss", # Ações
            "https://br.investing.com/rss/market_overview.rss", # Visão Geral
            "https://www.infomoney.com.br/feed/"
        ]
        self._cache = {}
        self._cache_expiry = 600 # 10 minutos

    async def fetch_all_news(self) -> List[Dict]:
        """Busca todas as notícias das fontes configuradas."""
        current_time = time.time()
        if "all_news" in self._cache and (current_time - self._cache["all_news"]["time"]) < self._cache_expiry:
            return self._cache["all_news"]["data"]

        all_entries = []
        async with httpx.AsyncClient() as client:
            for url in self.sources:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        feed = feedparser.parse(response.text)
                        for entry in feed.entries:
                            # Tentar extrair data para ordenação
                            dt = None
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                            
                            all_entries.append({
                                "title": entry.title,
                                "link": entry.link,
                                "published": entry.get("published", ""),
                                "date_obj": dt,
                                "source": "Investing" if "investing" in url else "InfoMoney",
                                "summary": entry.get("summary", "")[:200] + "..." if entry.get("summary") else ""
                            })
                except Exception as e:
                    print(f"Erro ao buscar RSS {url}: {e}")

        # Ordenar por data decrescente (mais recentes primeiro)
        all_entries.sort(key=lambda x: x["date_obj"] if x["date_obj"] else datetime.min, reverse=True)
        
        self._cache["all_news"] = {"data": all_entries, "time": current_time}
        return all_entries

    async def get_news_for_portfolio(self, search_terms: List[str], has_portfolio: bool = False) -> List[Dict]:
        """Filtra notícias. Se has_portfolio=True, retorna apenas se houver match."""
        all_news = await self.fetch_all_news()
        
        if not has_portfolio or not search_terms:
            return all_news[:6] # Limite de 6 notícias gerais

        filtered_news = []
        terms = [t.upper() for t in search_terms]
        
        for news in all_news:
            title_upper = news["title"].upper()
            summary_upper = news["summary"].upper()
            
            # Match estrito: o ticker ou termo deve estar presente
            if any(term in title_upper or term in summary_upper for term in terms):
                filtered_news.append(news)

        return filtered_news[:15]

news_service = NewsService()
