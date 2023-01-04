import json
import time

import requests
import yaml


class MyIntegration:

    def __init__(self):
        """
        Gets required variable data from config yaml file.
        """
        with open("my_variables.yml", 'r') as stream:
            try:
                self.my_variables_map = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print("[Error]: while reading yml file", exc)
        self.my_variables_map["CRYPTO_NOTION_ENTRIES"] = {}
        self.my_variables_map["STOCKS_NOTION_ENTRIES"] = {}
        self.getDatabaseIds()
        self.getCryptoDatabaseEntities()
        self.getStocksDatabaseEntities()

    def getDatabaseIds(self):
        url = "https://api.notion.com/v1/databases/"
        headers = {
            'Notion-Version': '2021-05-13',
            'Authorization':
                'Bearer ' + self.my_variables_map["MY_NOTION_SECRET_TOKEN"]
        }
        response = requests.request("GET", url, headers=headers)
        for database in response.json()["results"]:
            key = "CRYPTO_DATABASE_ID"
            if database["title"][0]["text"]["content"] == "Stocks":
                key = "STOCKS_DATABASE_ID"
            self.my_variables_map[key] = database["id"]

    def getCryptoDatabaseEntities(self):
        url = f"https://api.notion.com/v1/databases/{self.my_variables_map['CRYPTO_DATABASE_ID']}/query"
        headers = {
            'Notion-Version': '2021-05-13',
            'Authorization': 'Bearer ' + self.my_variables_map["MY_NOTION_SECRET_TOKEN"]
        }
        response = requests.request("POST", url, headers=headers)
        resp = response.json()
        for v in resp["results"]:
            if v["properties"]["Status"]["select"]["name"] == "Current":
                self.my_variables_map["CRYPTO_NOTION_ENTRIES"].update({v["properties"]["Ticker"]["rich_text"][0]["text"]["content"]: {"page": v["id"], "price": float(v["properties"]["Price"]["number"])}})

    def getStocksDatabaseEntities(self):
        url = f"https://api.notion.com/v1/databases/{self.my_variables_map['STOCKS_DATABASE_ID']}/query"
        headers = {
            'Notion-Version': '2021-05-13',
            'Authorization': 'Bearer ' + self.my_variables_map["MY_NOTION_SECRET_TOKEN"]
        }
        response = requests.request("POST", url, headers=headers)
        resp = response.json()
        for v in resp["results"]:
            if v["properties"]["Status"]["select"]["name"] == "Current":
                self.my_variables_map["STOCKS_NOTION_ENTRIES"].update({v["properties"]["Ticker"]["rich_text"][0]["text"]["content"]: {"page": v["id"], "price": float(v["properties"]["Price"]["number"])}})

    def getCryptoPrices(self):
        """
        Download the required crypto prices using Binance API.
        Ref: https://github.com/binance/binance-api-postman
        """
        for name, data in self.my_variables_map["CRYPTO_NOTION_ENTRIES"].items():
            url = f"https://api.binance.com/api/v3/avgPrice?"\
                f"symbol={name}USDT"
            response = requests.request("GET", url)
            if response.status_code == 200:
                content = response.json()
                data['price'] = content['price']

    def getStockPrices(self):
        """
        Download the required stock prices using Yahoo finance API.
        # Ref: https://syncwith.com/yahoo-finance/yahoo-finance-api
        """
        for name, data in self.my_variables_map["STOCKS_NOTION_ENTRIES"].items():
            url = f"https://query1.finance.yahoo.com/v11/finance/quoteSummary/{name}?modules=financialData"
            print("url?", url)
            response = requests.request("GET", url, headers = {'User-agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                content = response.json()
                data['price'] = content["quoteSummary"]["result"][0]["financialData"]["currentPrice"]["fmt"]

    def updateNotionDatabase(self, pageId, price):
        """
        A notion database (if integration is enabled) page with id `pageId`
        will be updated with the data `price`.
        """
        url = "https://api.notion.com/v1/pages/" + str(pageId)
        headers = {
            'Authorization':
                'Bearer ' + self.my_variables_map["MY_NOTION_SECRET_TOKEN"],
            'Notion-Version': '2021-05-13',
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "properties": {
                "Price": {
                    "type": "number",
                    "number": float(price),
                },
            }
        })
        print(requests.request(
                "PATCH", url, headers=headers, data=payload
            ).text)

    def UpdateIndefinitely(self):
        """
        Orchestrates downloading prices and updating the same
        in notion database.
        """
        # while True:
        try:
            self.getCryptoPrices()
            for _, data in self.my_variables_map["CRYPTO_NOTION_ENTRIES"].items():
                self.updateNotionDatabase(
                    pageId=data['page'],
                    price=data['price'],
                )
                time.sleep(0.5)
            self.getStockPrices()
            for _, data in self.my_variables_map["STOCKS_NOTION_ENTRIES"].items():
                self.updateNotionDatabase(
                    pageId=data['page'],
                    price=data['price'],
                )
                time.sleep(0.5)
            print("Prices updated")
            # time.sleep(1 * 60)
        except Exception as e:
            print(f"[Error encountered]: {e}")


if __name__ == "__main__":
    # With 😴 sleeps to prevent rate limit from kicking in.
    MyIntegration().UpdateIndefinitely()
