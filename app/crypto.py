import requests

class Crypto:
  def getPrice(self, symbol):
    """
    Download the required crypto prices using Binance API.
    Ref: https://github.com/binance/binance-api-postman
    """
    url = f"https://api.binance.com/api/v3/avgPrice?"\
            f"symbol={symbol}USDT"
    response = requests.request("GET", url)
    if response.status_code == 200:
      content = response.json()
      return content['price']
