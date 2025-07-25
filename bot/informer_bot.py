import sys
import json
import time

from datetime import datetime

import telebot
from telebot import types

from botscontroller import BotsController

bc = BotsController()

try:
    parametersDict = {}
    
    with open('bot/key.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
except Exception as e:
    print(f'Ошибка при чтении ссылки! {e}')
    sys.exit(1)
    
bot = telebot.TeleBot(parametersDict['key'])

print('Бот успешно инициирован!')

@bot.message_handler(commands=["start"])
def start(message):
    if (message.chat.id in parametersDict['admins']):
        listCommand = [
            'Получить информацию о продажах за прошлый день',
            'Получить детализацию'
        ]
        
        markup = bc.GenerateButtonArrays(listCommand)
        
        bot.send_message(message.chat.id, f'Приветствую, {message.from_user.first_name}! Чем я могу помочь сегодня?', reply_markup=markup)
    else:
        markup = bc.GenerateButtonArrays()
        
        bot.send_message(message.chat.id, 'Приветствую! Я для получения служебной информации! Если вы не знаете что со мной делать, то это значит, что я предназначен не для вас, спасибо за внимание!', reply_markup=markup)

@bot.message_handler(content_types=["text"])
def func(message):
    if (message.chat.id in parametersDict['admins']):
        if message.text == 'Получить информацию о продажах за прошлый день':
            pass
        elif message.text == "Получить детализацию":
            pass
        else:
            markup = bc.GenerateButtonArrays()
            bot.send_message(message.chat.id, "Я не знаю такой команды! Вы можете перезапустить меня, если что-то пошло не так!", reply_markup=markup)
    else:
        markup = bc.GenerateButtonArrays()
        bot.send_message(message.chat.id, "Я вас не знаю! Вы не авторизованы!", reply_markup=markup)

while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        file = open('Error_log.txt', 'a')
        file.write(f'{datetime.now()} - {e}\n')
        time.sleep(5)
        continue
