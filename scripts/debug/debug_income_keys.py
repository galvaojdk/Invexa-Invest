import yfinance as yf
import json

tickers = ["WEGE3.SA", "HGLG11.SA", "MXRF11.SA"]

for t in tickers:
    print(f"--- {t} ---")
    info = yf.Ticker(t).info
    print(f"Net Income To Common: {info.get('netIncomeToCommon')}")
    print(f"Net Income: {info.get('netIncome')}")
    print(f"Trailing Earnings: {info.get('trailingEarnings')}")
    # Print potential keys containing 'Income' or 'Revenue' or 'Earnings'
    keys = [k for k in info.keys() if 'Income' in k or 'Earnings' in k or 'Profit' in k]
    print(f"Related Keys: {keys}")
