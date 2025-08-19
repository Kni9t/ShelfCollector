import json
import time
import sys
import logging

from datetime import datetime

from collector.shelf_collector import ShelfCollector
from collector.sales_db_controller import DBController
from collector.time_controller import TimeController

try:
    logging.basicConfig(filename = 'collector.log', encoding = 'utf-8', level=logging.DEBUG, format='%(name)s: %(asctime)s - %(levelname)s - %(filename)s - %(module)s - %(lineno)d - %(message)s')
    logging.getLogger("imapclient.imaplib").setLevel(logging.WARNING)
    logging.getLogger("imapclient.imapclient").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    
    logger = logging.getLogger('main_logger')
    
except Exception as e:
    msg = f'{datetime.now()} - Ошибка при настройке логгера для сборщика! {e}'
    print(msg)
        
    with open('collector_error_log.txt', 'a', encoding = 'utf-8') as file:
        file.write(msg + '\n')
        file.close()
    sys.exit(1)

parametersDict = {}
try:
    with open('params/parameters.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
except Exception as e:
    msg = f'Ошибка при загрузке параметров! [{e}]'
    
    print(f'{datetime.now()} - {msg}')
    logger.error(msg)
    sys.exit(1)
    
try:
    Collector = ShelfCollector(parametersDict['url'], parametersDict['glogin'], parametersDict['gpass'])
    logger.debug('ShelfCollector успешно инициирован!')
    
    Timer = TimeController()
    logger.debug('TimeController успешно инициирован!')
    
    SQL = DBController()
    logger.debug('DBController успешно инициирован!')
except Exception as e:
    msg = f'Ошибка при инициировании основных классов! [{e}]'
    
    print(f'{datetime.now()} - {msg}')
    logger.error(msg)
    sys.exit(1)

SQL.InitMainTables()

while True:
    try:
        dataList = []
        
        dataList.append(Collector.CollectSalesWolf())
        logger.info(f'Данные с полки Волчка успешно собраны!')
        
        dataList.append(Collector.CollectSalesPolks())
        logger.info(f'Данные с полки Полкиус успешно собраны!')
        
        dataList.append(Collector.CollectSalesFox())
        logger.info(f'Данные с Лисьей полки успешно собраны!')
        
        for data in dataList:
            if (data != []) and (data is not None):
                SQL.AddShelfSale(data)
        
        msg = f'Данные за сегодня успешно собраны'
        print(msg)
        logger.info(msg)
        
        second, nextDate = Timer.CalculationWaitTime()
        
        msg = f'Ожидание до {nextDate}'
        print(msg)
        logger.info(msg)
        
        time.sleep(second)
        
    except Exception as e:
        msg = f'Ошибка при сборе данных! {e}'
        
        print(f'{datetime.now()} - {msg}')
        logger.error(msg)
        
        time.sleep(5)