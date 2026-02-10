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
                            all_entries.append({
                                "title": entry.title,
                                "link": entry.link,
                                "published": entry.get("published", ""),
                                "source": url.split(".")[1], # Simplificado
                                "summary": entry.get("summary", "")[:200] + "..."
                            })
                except Exception as e:
                    print(f"Erro ao buscar RSS {url}: {e}")

        self._cache["all_news"] = {"data": all_entries, "time": current_time}
        return all_entries

    async def get_news_for_portfolio(self, tickers: List[str]) -> List[Dict]:
        """Filtra notícias relevantes para os tickers fornecidos."""
        all_news = await self.fetch_all_news()
        if not tickers:
            return all_news[:10]

        filtered_news = []
        # Normalizar tickers (ex: PETR4)
        search_terms = [t.upper() for t in tickers]
        
        for news in all_news:
            title_upper = news["title"].upper()
            summary_upper = news["summary"].upper()
            
            # Verifica se algum ticker aparece no título ou resumo
            is_relevant = any(term in title_upper or term in summary_upper for term in search_terms)
            
            if is_relevant:
                filtered_news.append(news)

        # Se não houver notícias específicas pros tickers, retorna as últimas gerais
        if not filtered_news:
            return all_news[:10]

        return filtered_news[:15] # Limitar a 15 notícias

news_service = NewsService()
