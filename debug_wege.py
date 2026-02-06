import yfinance as yf
import json

ticker = yf.Ticker("WEGE3.SA")
info = ticker.info

print(f"Shares Outstanding: {info.get('sharesOutstanding')}")
print(f"Implied Shares Outstanding: {info.get('impliedSharesOutstanding')}")
print(f"Market Cap: {info.get('marketCap')}")
