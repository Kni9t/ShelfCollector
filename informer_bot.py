import time

from datetime import datetime

from bot import Bot

TelegramBot = Bot()

while True:
    try:
        TelegramBot.Run()
        
    except Exception as e:
        err = f'{datetime.now()} - Ошибка при работе бота! {e}'
        
        with open('error_log.txt', 'a', encoding = 'utf-8') as file:
            file.write(err + '\n')
            file.close()
        time.sleep(5)
