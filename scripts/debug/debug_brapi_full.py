import httpx
import json
import asyncio

# Token from app/services/market_data.py
BRAPI_TOKEN = "5y8qbu4kibxgcT3YQxG1XK"

async def debug_brapi():
    tickers = "WEGE3,HGLG11" # Teste com Ação e FII
    # Adding modules query param
    modules = "summaryProfile,defaultKeyStatistics,financialData"
    url = f"https://brapi.dev/api/quote/{tickers}?fundamental=true&modules={modules}&token={BRAPI_TOKEN}"
    
    print(f"Fetching {url}...")
    
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=20)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            # Save to file
            with open("brapi_dump.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("Response saved to brapi_dump.json")
        else:
            print(f"Error: {r.text}")

if __name__ == "__main__":
    asyncio.run(debug_brapi())
