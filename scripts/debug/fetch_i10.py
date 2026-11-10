import httpx
import asyncio

async def fetch_i10():
    ticker = "WEGE3"
    url = f"https://investidor10.com.br/acoes/{ticker.lower()}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    print(f"Fetching {url}...")
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        r = await client.get(url, headers=headers)
        if r.status_code == 200:
            with open("debug_i10_stock.html", "w", encoding="utf-8") as f:
                f.write(r.text)
            print("Saved to debug_i10_stock.html")
        else:
            print(f"Failed: {r.status_code}")

if __name__ == "__main__":
    asyncio.run(fetch_i10())
