import json
import time
import sys

from datetime import datetime

from collector.shelf_collector import ShelfCollector
from collector.sales_db_controller import DBController
from collector.time_controller import TimeController

parametersDict = {}
try:
    with open('params/parameters.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
except Exception as e:
    err = f'{datetime.now()} - Ошибка при загрузке параметров! {e}'
        
    with open('collector_error_log.txt', 'a', encoding = 'utf-8') as file:
        file.write(err + '\n')
        file.close()
    sys.exit(1)

Collector = ShelfCollector(parametersDict['url'], parametersDict['glogin'], parametersDict['gpass'])
Timer = TimeController()
SQL = DBController()

SQL.InitMainTables()

while True:
    try:
        dataList = []
        dataList.append(Collector.CollectSalesWolf())
        dataList.append(Collector.CollectSalesPolks())
        dataList.append(Collector.CollectSalesFox())
        
        for data in dataList:
            if data != []:
                SQL.AddShelfSale(data)
        
        print(f'Данные за сегодня успешно собраны')
        second, nextDate = Timer.CalculationWaitTime()
        
        print(f'Ожидание до {nextDate}')
        time.sleep(second)
        
    except Exception as e:
        err = f'{datetime.now()} - Ошибка при сборе данных! {e}'
        
        with open('collector_error_log.txt', 'a', encoding = 'utf-8') as file:
            file.write(err + '\n')
            file.close()