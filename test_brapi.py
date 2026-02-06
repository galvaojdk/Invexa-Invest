import httpx
import json

TOKEN = "public" # Brapi has a "public" token with limits, or usually works for few reqs.
# Or does Brapi require specific token?
# "https://brapi.dev/api/quote/PETR4?fundamental=true"

async def test():
    tickers = "WEGE3,HGLG11"
    url = f"https://brapi.dev/api/quote/{tickers}?fundamental=true&token=public"
    
    # Note: Using 'token' param often helps avoid rate limits or get "real" data if user has one.
    # Without token it might be limited.
    # I'll try without first.
    
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(json.dumps(data, indent=2))
        else:
            print(r.text)

import asyncio
if __name__ == "__main__":
    asyncio.run(test())
