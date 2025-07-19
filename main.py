import json

from shelfcollector import ShelfCollector
from sqlcontroller import SQLController

parametersDict = {}
try:
    with open('link.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
except Exception as e:
    print(f'Ошибка при чтении ссылки! {e}')

Collector = ShelfCollector(parametersDict['url'])
SQL = SQLController()

SQL.CreateTable()

print(Collector.CollectSales())
