import sys
import json
import time

from datetime import datetime, timedelta

import telebot
from telebot import types

from botscontroller import BotsController
from sqlcontroller import SQLController

bc = BotsController()

try:
    parametersDict = {}
    
    with open('key.json') as file:
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
            "Получить информацию о продажах за прошлый день",
            "Получить детализацию"
        ]
        
        markup = bc.GenerateButtonArrays(listCommand)
        
        bot.send_message(message.chat.id, f'Приветствую, {message.from_user.first_name}! Чем я могу помочь сегодня?', reply_markup = markup)
    else:
        markup = bc.GenerateButtonArrays()
        
        bot.send_message(message.chat.id, 'Приветствую! Я для получения служебной информации! Если вы не знаете что со мной делать, то это значит, что я предназначен не для вас, спасибо за внимание!', reply_markup=markup)

@bot.message_handler(content_types=["text"])
def func(message):
    if (message.chat.id in parametersDict['admins']):
        if message.text == "Получить информацию о продажах за прошлый день":
            date = (datetime.now() - timedelta(days = 1)).strftime('%Y-%m-%d')
            query = f'SELECT sh.name AS shelf_name, SUM(s.revenue) AS total_revenue, s.date FROM sales s join shelves sh on s.shelf_id = sh.shelf_id WHERE s.date = "{date}" GROUP BY sh.name;'
            
            SQL = SQLController()
            
            rows = SQL.SendQuery(query)
            resultString = f'Данные на {date}\n'
            
            for row in rows:
                resultString += f'{row[0]} - {row[1]} руб.\n'
                
            listCommand = [
            "Получить информацию о продажах за прошлый день",
            "Получить детализацию"
            ]
        
            markup = bc.GenerateButtonArrays(listCommand)
            bot.send_message(message.chat.id, f'{resultString}', reply_markup = markup)
            
        elif message.text == "Получить детализацию":
            listCommand = [
            "По всем дням в этом месяце",
            "По всем месяцам в этом году"
            ]
        
            markup = bc.GenerateButtonArrays(listCommand)
            bot.send_message(message.chat.id, f'Какую детализацию вы хотели бы получить?', reply_markup = markup)
        
        elif message.text == "По всем дням в этом месяце":
            date = datetime.now().strftime('%m')
            query = f"SELECT strftime('%m-%d', s.date) AS day, sh.name AS shelf_name, SUM(s.revenue) AS total_revenue, COUNT(*) AS num_sales FROM sales s JOIN shelves sh ON s.shelf_id = sh.shelf_id WHERE strftime('%m', s.date) = '{date}' GROUP BY day, sh.name ORDER BY day, sh.name;"
            
            SQL = SQLController()
            rows = SQL.SendQuery(query)
            
            resultString = f'Данные на месяц {date} в формате:\nдень, полка, суммарный доход, число продаж\n'
            
            for row in rows:
                resultString += f'{row[0]} - {row[1]} - {row[2]} руб. - {row[3]} шт.\n'
                
            markup = bc.GenerateButtonArrays()
            bot.send_message(message.chat.id, f'{resultString}', reply_markup = markup)
        
        elif message.text == "По всем месяцам в этом году":
            date = datetime.now().strftime('%Y')
            query = f"SELECT strftime('%Y-%m', s.date) AS month, sh.name AS shelf_name, SUM(s.revenue) AS total_revenue, COUNT(*) AS num_sales FROM sales s JOIN shelves sh ON s.shelf_id = sh.shelf_id WHERE strftime('%Y', s.date) = '{date}' GROUP BY month, sh.name ORDER BY month, sh.name;"
            
            SQL = SQLController()
            rows = SQL.SendQuery(query)
            
            resultString = f'Данные на {date} год в формате:\nмесяц, полка, суммарный доход, число продаж\n'
            
            for row in rows:
                resultString += f'{row[0]} - {row[1]} - {row[2]} руб. - {row[3]} шт.\n'
                
            markup = bc.GenerateButtonArrays()
            bot.send_message(message.chat.id, f'{resultString}', reply_markup = markup)
            
        else:
            markup = bc.GenerateButtonArrays()
            bot.send_message(message.chat.id, "Я не знаю такой команды! Вы можете перезапустить меня, если что-то пошло не так!", reply_markup = markup)
    else:
        markup = bc.GenerateButtonArrays()
        bot.send_message(message.chat.id, "Я вас не знаю! Вы не авторизованы!", reply_markup=markup)

while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        err = f'{datetime.now()} - Ошибка при работе бота! {e}'
        
        with open('error_log.txt', 'a') as file:
            file.write(err)
            file.close()
        time.sleep(5)
        continue
