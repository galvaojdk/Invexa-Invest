import yfinance as yf
import json

ticker = yf.Ticker("KNIP11.SA")
info = ticker.info

# Filter large keys for readability if needed, or just print keys
print(json.dumps(info, indent=2))
