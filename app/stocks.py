import requests

class Stocks:
  def getPrice(self, symbol):
    """
    Download the required stock prices using Yahoo finance API.
    # Ref: https://syncwith.com/yahoo-finance/yahoo-finance-api
    """
    url = f"https://query1.finance.yahoo.com/v11/finance/quoteSummary/{symbol}?modules=financialData"
    response = requests.request("GET", url, headers = {'User-agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        content = response.json()
        return content["quoteSummary"]["result"][0]["financialData"]["currentPrice"]["fmt"]
