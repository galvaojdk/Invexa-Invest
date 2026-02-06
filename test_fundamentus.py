import httpx
import re

async def get_fundamentus(ticker):
    url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker}"
    print(f"Fetching {ticker} from {url}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, follow_redirects=True)
        html = r.text
        
        # Simple Regex extraction for quick test (Soup is better but I want to avoid installing if possible)
        # Look for "Lucro Líquido"
        # Table structure is complex, Regex might be fragile.
        # But let's try to find keys.
        
        # Shares (No Acoes / Cotas)
        # <span>Nro. Ações:</span><span class="txt">4.197.317.998</span>
        shares = re.search(r'<span>Nro\. (?:Ações|Cotas):</span>.*?<span class="txt">([\d\.,]+)</span>', html, re.DOTALL)
        
        # Net Income (Lucro Líquido - 12m)
        # <span>Lucro Líquido</span>.*?<span class="txt">(\d+)</span> NO.
        # It usually is in a table.
        
        # Let's just print finding "Lucro Líquido" context
        print(f"Shares raw: {shares.group(1) if shares else 'Not Found'}")
        
        if "Lucro Líquido" in html:
            print("Found 'Lucro Líquido' label.")
        else:
            print("Did NOT find 'Lucro Líquido'.")

        # FII specific: "Patrimônio Líquido" implies Book Value?
        if "Patrimônio Líquido" in html:
            print("Found 'Patrimônio Líquido'.")

import asyncio
if __name__ == "__main__":
    asyncio.run(get_fundamentus("WEGE3"))
    asyncio.run(get_fundamentus("HGLG11"))
