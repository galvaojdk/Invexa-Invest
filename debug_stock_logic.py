
import asyncio
import httpx
import json

BRAPI_TOKEN = "5y8qbu4kibxgcT3YQxG1XK"

async def debug_brapi_stock(ticker):
    modules = "summaryProfile,defaultKeyStatistics,financialData"
    url = f"https://brapi.dev/api/quote/{ticker}?fundamental=true&modules={modules}&token={BRAPI_TOKEN}"
    print(f"Fetching {ticker} via Brapi...")
    
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        if r.status_code != 200:
            print(f"Error: {r.status_code}")
            return
            
        data = r.json()
        results = data.get('results', [])
        for item in results:
            symbol = item.get('symbol')
            print(f"--- Symbol: {symbol} ---")
            
            dk_stats = item.get('defaultKeyStatistics') or {}
            fin_data = item.get('financialData') or {}
            
            # Trace extraction
            lpa = dk_stats.get('trailingEps') or item.get('earningsPerShare')
            shares = dk_stats.get('sharesOutstanding')
            
            print(f"LPA (Eps): {lpa}")
            print(f"Shares: {shares}")
            
            net_income_raw = dk_stats.get('netIncomeToCommon')
            print(f"Net Income Raw (dk_stats): {net_income_raw}")
            
            if not net_income_raw:
                print("Calculating/Fallback Net Income...")
                if lpa and shares:
                    calc = lpa * shares
                    print(f"Calculated from LPA*Shares: {calc}")
                elif fin_data.get('profitMargins') and fin_data.get('totalRevenue'):
                    pm = fin_data.get('profitMargins')
                    rev = fin_data.get('totalRevenue')
                    print(f"ProfitMargins: {pm}, Revenue: {rev}")
                    calc = pm * rev
                    print(f"Calculated from Margin*Rev: {calc}")
                else:
                     print("FALLBACK FAILED. Data missing.")
            else:
                 print(f"Using Raw Net Income: {net_income_raw}")

if __name__ == "__main__":
    asyncio.run(debug_brapi_stock("TAEE11"))
    asyncio.run(debug_brapi_stock("WEGE3"))
