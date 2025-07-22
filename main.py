import json
import time
import sys

from shelfcollector import ShelfCollector
from sqlcontroller import SQLController
from timecontroller import TimeController

parametersDict = {}
try:
    with open('parameters.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
except Exception as e:
    print(f'Ошибка при чтении ссылки! {e}')
    sys.exit(1)

Collector = ShelfCollector(parametersDict['url'], parametersDict['glogin'], parametersDict['gpass'])
Timer = TimeController()
SQL = SQLController()

SQL.CreateTable()

while True:
    try:
        dataList = []
        dataList.append(Collector.CollectSalesWolf())
        dataList.append(Collector.CollectSales('shop@polkius.ru'))
        
        for data in dataList:
            if len(data) != 0:
                result, err = SQL.DataInsert(data)
                
                if not result:
                    print(f'Ошибка при добавлении данных в БД: {err}')
            else:
                print(f'Данных о продажах за сегодня нету!')
        
        print(f'Данные за сегодня успешно собраны')
        second, nextDate = Timer.CalculationWaitTime()
        
        print(f'Ожидание до {nextDate}')
        time.sleep(second)
        
    except Exception as e:
        print(f'Ошибка при сборе данных! {e}')