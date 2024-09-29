import yfinance as yf


btc = yf.Ticker("BTC-USD")

# Obter dados históricos (desde 2014)
data = btc.history(start="2014-01-01", end='2024-01-01')

print(data)