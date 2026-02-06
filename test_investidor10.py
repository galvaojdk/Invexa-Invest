import httpx
import re
import asyncio

async def test_investidor10(ticker):
    url = f"https://investidor10.com.br/fiis/{ticker.lower()}/"
    print(f"Fetching {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            print(f"Failed: {r.status_code}")
            return
            
        html = r.text
        print(f"HTML Length: {len(html)}")
        
        # Extract DY
        # <div class="_card-body"><span>10,87%</span></div>
        # Need to be specific. Usually Investidor10 has cards. Dictionary-like structures are hard with Regex but let's look for specific labels.
        # "Dividend Yield" -> next value.
        
        # Debug DY context - Card style
        idx = html.find('title="Dividend Yield"')
        if idx != -1:
            print(f"Context DY Card: {html[idx:idx+200]}")
            
        # Regex approach for DY
        # Pattern: <span title="Dividend Yield">Dividend Yield</span>...
        dy_match = re.search(r'title="Dividend Yield".*?_card-body.*?<span>([\d,]+)%</span>', html, re.DOTALL)
        if dy_match:
            print(f"DY: {dy_match.group(1)}")
        else:
            print("DY Not Found")
            
        # Search for Lucro or Patrimonio
        # P/VP is done.
        
        # Debug Lucro
        # Often "Último Rendimento" is prominent.
        # Maybe "Valor Patrimonial" (which is VPA * Shares approx)?
        # Debug Price Card
        idx_price_card = html.find('title="Cotação"')
        if idx_price_card != -1:
             print(f"Context Price Card: {html[idx_price_card:idx_price_card+200]}")
             
        # Regex for Price
        # Context: title="Cota..." ... _card-body ... <span class="value">R$ 156,95</span>
        price_match = re.search(r'title="Cota.*?".*?_card-body.*?(?:class="value">|<span>)R\$\s*([\d,]+)', html, re.DOTALL)
        if price_match:
             print(f"Price: {price_match.group(1)}")
        else:
             print("Price Not Found")
        # Let's search for "Patrim"
        idx_pat = html.find("Patrim")
        if idx_pat != -1:
             print(f"Context Patrim: {html[idx_pat-50:idx_pat+200]}")

        # Search for "Lucro"
        idx_lucro = html.find("Lucro")
        if idx_lucro != -1:
             print(f"Context Lucro: {html[idx_lucro-50:idx_lucro+200]}")
        # Restore P/VP search
        pvp_match = re.search(r'P/VP</span>.*?_card-body.*?<span>([\d,]+)</span>', html, re.DOTALL)
        if pvp_match:
            print(f"P/VP: {pvp_match.group(1)}")
            
        # Extract Cotas
        # Context: <span class="text">Cotas</span> ... <span ...>33.784.664</span> (Example)
        # Extract Cotas specific anchored to label
        # Context: ... "Cotas" ... box quota-value ... span value
        cotas_match_2 = re.search(r'Cotas</span>.*?class="box quota-value".*?<span>(.*?)</span>', html, re.DOTALL)
        if cotas_match_2:
             # Clean up: "33.784.664" might have whitespace
             raw = cotas_match_2.group(1).strip()
             print(f"Cotas Final: {raw}")
        else:
             print("Cotas (quota-value) Not Found")

        # Debug: search for "Dados do Fundo"
        idx_dados = html.find('Dados do Fundo')
        if idx_dados != -1:
             print(f"Context Dados: {html[idx_dados:idx_dados+500]}")

            
        # Liquidez Daily
        # <span class="title">Liquidez Diária</span>.*?<span>R\$ ([\d\.,]+)</span>
        
        # Valorização (Cotação base check)
        
if __name__ == "__main__":
    asyncio.run(test_investidor10("hglg11"))
    asyncio.run(test_investidor10("mxrf11"))
