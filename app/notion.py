import json
import time

import requests
import yaml

from crypto import Crypto
from stocks import Stocks

class Integration:
    def __init__(self):
        """
        Gets required variable data from config yaml file.
        """
        with open("config.yml", 'r') as stream:
            try:
                self.config_map = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print("[Error]: while reading yml file", exc)

        self.notion_base_url = self.config_map["NOTION_BASE_URL"]
        self.notion_secret = self.config_map["NOTION_SECRET"]
        self.crypto_database = "Crypto"
        self.stocks_database = "Stocks"
        self.databases = [self.crypto_database, self.stocks_database]
        self.entries = {
            self.crypto_database: {},
            self.stocks_database: {} 
        }

        self.getDatabases(self.databases)

        for database in self.databases: 
            self.getDatabaseEntities(database)        

    def getRequestHeaders(self):
        return {
            'Notion-Version': '2021-05-13',
            'Content-Type': 'application/json',
            'Authorization':
                'Bearer ' + self.notion_secret
        }

    def getDatabases(self, databases):
        url = self.notion_base_url + "/databases/"
        response = requests.request("GET", url, headers=self.getRequestHeaders())
        for database in response.json()["results"]:
            database_name = database["title"][0]["text"]["content"]
            if database_name in databases:
                self.config_map[database_name] = database["id"]

    def getDatabaseEntities(self, database):
        url = f"{self.notion_base_url}/databases/{self.config_map[database]}/query"
        response = requests.request("POST", url, headers=self.getRequestHeaders())
        resp = response.json()
        for v in resp["results"]:
            if v["properties"]["Status"]["select"]["name"] == "Current":
                self.entries[database].update({v["properties"]["Ticker"]["rich_text"][0]["text"]["content"]: {"page": v["id"], "price": float(v["properties"]["Price"]["number"])}})

    def updateNotionDatabase(self, pageId, price):
        """
        A notion database (if integration is enabled) page with id `pageId`
        will be updated with the data `price`.
        """
        url = self.notion_base_url + "/pages/" + str(pageId)
        payload = json.dumps({
            "properties": {
                "Price": {
                    "type": "number",
                    "number": float(price),
                },
            }
        })
        print(requests.request(
                "PATCH", url, headers=self.getRequestHeaders(), data=payload
            ).text)

    def UpdatePrices(self):
        """
        Orchestrates downloading prices and updating the same
        in notion database.
        """
        try:
            for name, data in self.entries[self.crypto_database].items():
                price = Crypto().getPrice(name)
                if price:
                    self.updateNotionDatabase(data['page'], price)
                    time.sleep(0.5)

            for name, data in self.entries[self.stocks_database].items():
                price = Stocks().getPrice(name)
                if price:
                    self.updateNotionDatabase(data['page'], price)
                    time.sleep(0.5)

            print("Prices updated")
        except Exception as e:
            print(f"[Error encountered]: {e}")
