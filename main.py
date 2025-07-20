import json
import time
import sys

from shelfcollector import ShelfCollector
from sqlcontroller import SQLController
from timecontroller import TimeController

parametersDict = {}
try:
    with open('link.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
except Exception as e:
    print(f'Ошибка при чтении ссылки! {e}')
    sys.exit(1)

Collector = ShelfCollector(parametersDict['url'])
Timer = TimeController()
SQL = SQLController()

SQL.CreateTable()

while True:
    try:
        data = Collector.CollectSales()
        
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