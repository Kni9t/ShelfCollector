import time
import json
import sys
import logging

from datetime import datetime

from bots.informer_bot import InformerBot

try:
    logging.basicConfig(filename = 'bot.log', encoding = 'utf-8', level=logging.DEBUG, format='%(name)s: %(asctime)s - %(levelname)s - %(filename)s - %(module)s - %(lineno)d - %(message)s')
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logger = logging.getLogger('main')
except Exception as e:
    err = f'{datetime.now()} - Ошибка при настройке логгера бота! {e}'
    print(err)
        
    with open('bot_error_log.txt', 'a', encoding = 'utf-8') as file:
        file.write(err + '\n')
        file.close()
    sys.exit(1)

try:
    fileName = 'params/parameters.json'
    with open(fileName) as file:
        parametersDict = dict(json.load(file))
        file.close()
    logger.debug(f'Файл {fileName} успешно загружен!')
    
    fileName = 'params/buttons_list.json'
    with open(fileName, encoding = 'utf-8') as file:
        buttons_list = dict(json.load(file))
        file.close()
    logger.debug(f'Файл {fileName} успешно загружен!')
    
except Exception as e:
    err = f'Ошибка при загрузке параметров бота! {e}'
    
    logger.error(err)
    print(err)
    sys.exit(1)

TelegramBot = InformerBot(parametersDict, buttons_list)

while True:
    try:
        TelegramBot.Run()
        
    except Exception as e:
        err = f'Ошибка при работе бота! {e}'
        
        logger.error(err)
        print(err)
        
        time.sleep(5)
