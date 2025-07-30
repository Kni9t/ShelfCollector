import time

from datetime import datetime

from bot import Bot

TelegramBot = Bot()

while True:
    try:
        TelegramBot.Run()
        
    except Exception as e:
        err = f'{datetime.now()} - Ошибка при работе бота! {e}'
        
        with open('error_log.txt', 'a') as file:
            file.write(err)
            file.close()
        time.sleep(5)
