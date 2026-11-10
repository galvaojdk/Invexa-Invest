import asyncio
import httpx

BRAPI_TOKEN = "5y8qbu4kibxgcT3YQxG1XK"

async def debug_brapi_volume(ticker="PETR4"):
    modules = "summaryProfile,defaultKeyStatistics,financialData"
    url = f"https://brapi.dev/api/quote/{ticker}?fundamental=true&modules={modules}&token={BRAPI_TOKEN}"
    print(f"Fetching {ticker} from {url}...")
    
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code != 200:
            print(f"Error: {r.status_code}")
            return
            
        data = r.json()
        results = data.get('results', [])
        if not results:
            print("No results found.")
            return
            
        item = results[0]
        price = item.get('regularMarketPrice')
        vol = item.get('regularMarketVolume')
        
        dk_stats = item.get('defaultKeyStatistics') or {}
        avg_vol_3m = dk_stats.get('averageDailyVolume3Month')
        
        print(f"\n--- Data for {ticker} ---")
        print(f"Price: {price}")
        print(f"Regular Volume (root): {vol}")
        print(f"Avg Vol 3M (dk_stats): {avg_vol_3m}")
        
        used_vol = avg_vol_3m if (avg_vol_3m and avg_vol_3m > 0) else vol
        
        if used_vol and price:
            liquidity = used_vol * price
            print(f"Calculated Liquidity: {liquidity:,.2f}")
            print(f"Is > 1 Million? {liquidity > 1000000}")
        else:
            print("Could not calculate liquidity (missing price or volume)")

if __name__ == "__main__":
    asyncio.run(debug_brapi_volume())
