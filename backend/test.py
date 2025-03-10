import yfinance as yf
stock = yf.Ticker("INFY.NS")
hist = stock.history(period="1d")
print(hist)
