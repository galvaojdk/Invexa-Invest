import httpx
import asyncio

BRAPI_TOKEN = "5y8qbu4kibxgcT3YQxG1XK"

async def test_dividends():
    ticker = "WEGE3"
    # Tentando adicionar 'dividends' e 'balanceSheetHistory' (apenas para ver o que vem)
    modules = "dividends,summaryProfile" 
    url = f"https://brapi.dev/api/quote/{ticker}?fundamental=true&modules={modules}&token={BRAPI_TOKEN}"
    
    print(f"Fetching {url}...")
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # Print keys in result
            results = data.get('results', [])[0]
            print("Keys available:", results.keys())
            if 'dividendsData' in results:
                 print("dividendsData found!")
                 print(results['dividendsData'][:2]) # Print first 2
            else:
                 print("No 'dividendsData' key found directly.")
                 
            # Check if it is inside structure
            print("Full Data Sample:", str(results)[:500])

if __name__ == "__main__":
    asyncio.run(test_dividends())
