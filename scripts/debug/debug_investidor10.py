from app.services.importer import ImportService
import httpx
import re

import httpx
import re
import json

url = "https://investidor10.com.br/wallet/public/80897"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://investidor10.com.br/wallet/public/80897",
    "x-nextjs-data": "1"
}

print(f"1. Fetching Main HTML: {url}...")
try:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        # First get HTML to get cookies/buildId
        del headers["x-nextjs-data"] 
        response = client.get(url, headers=headers)
        html = response.text
        
        # Check text content for tickers (Deep Search)
        print("Searching for 'PETR' in HTML...")
        if "PETR" in html: print("FOUND PETR")
        else: print("NOT FOUND PETR")
        
        # Extract buildId
        build_id = "sm_u0qTNCPtwzpt-Sk4wg" # Hardcoded fallback
        match = re.search(r'"buildId":"(.*?)"', html)
        if match:
             build_id = match.group(1)
             print(f"Found Build ID: {build_id}")

        # JSON URL
        json_url = f"https://investidor10.com.br/wallet/_next/data/{build_id}/br/public/80897.json"
        print(f"2. Fetching Data JSON: {json_url}...")
        
        headers["x-nextjs-data"] = "1"
        
        resp_json = client.get(json_url, headers=headers)
        print(f"JSON Status: {resp_json.status_code}")
        print(f"JSON URL: {resp_json.url}")
        
        if resp_json.status_code == 200:
            data = resp_json.json()
            # Inspect structure
            page_props = data.get("pageProps", {})
            wallet = page_props.get("wallet", {})
            print(f"Wallet Name: {wallet.get('name')}")
            
            # Try to find assets
            # Usually in 'wallet' -> 'items' OR 'positions'
            print("Wallet Keys:", wallet.keys())
            
        else:
             print("JSON Content Type:", resp_json.headers.get("content-type"))
             # If html, it might be the page again
             if "text/html" in resp_json.headers.get("content-type", ""):
                 print("Received HTML instead of JSON. Redirected?")

except Exception as e:
    print(f"Error: {e}")
