import time
import json
import sys

from datetime import datetime

from bots.informer_bot import InformerBot

try:
    with open('params/parameters.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
    
    with open('params/buttons_list.json', encoding = 'utf-8') as file:
        buttons_list = dict(json.load(file))
        file.close()    
    
except Exception as e:
    err = f'{datetime.now()} - Ошибка при загрузке параметров! {e}'
        
    with open('collector_error_log.txt', 'a', encoding = 'utf-8') as file:
        file.write(err + '\n')
        file.close()
    sys.exit(1)

TelegramBot = InformerBot(parametersDict, buttons_list)

while True:
    try:
        TelegramBot.Run()
        
    except Exception as e:
        err = f'{datetime.now()} - Ошибка при работе бота! {e}'
        
        with open('bot_error_log.txt', 'a', encoding = 'utf-8') as file:
            file.write(err + '\n')
            file.close()
        time.sleep(5)
