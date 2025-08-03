import telebot
from telebot import types
import sys
import json
from datetime import datetime, timedelta

from collector.sales_db_controller import DBController
from collector.state_controller import StateController

class InformerBot:
    def __init__(self, parameters: dict, buttonsList: dict):
        
        self.parameters = parameters
        self.ButtonsList = buttonsList
        
        self.StateController = StateController('params/buf_users_state.json')
        
        self.bot = telebot.TeleBot(self.parameters['key'])
        
        self.bot.message_handler(commands=["start"])(self.StartCommand)
        self.bot.message_handler(content_types=["text"])(self.MainFunc)
        
        print('Бот успешно инициирован!')
        
    def StartCommand(self, message):
        if (self.CheckAllowUsers(message, self.parameters['admins'])):
            self.SendMessage(message, f'Приветствую, {message.from_user.first_name}! Чем я могу помочь сегодня?', self.ButtonsList['AdminMainMenuButtonList'])
        else:
            self.SendMessage(message, 'Приветствую! Я система по учету продаж на маркетах! Я принадлежу [Hlorkens](https://vk.com/hlorkens)', self.ButtonsList['MainMenuButtonList'])
    
    def MainFunc(self, message):
        if (message.text == "Получить информацию о продажах по полкам") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.SendMessage(message, f"Какую детализацию вы хотели бы получить?", self.ButtonsList['DetailShelfButtonList'])
            
        elif (message.text in self.ButtonsList['DetailShelfButtonList']) and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Get_Shelf_Detail(message)
            
        else:
            self.SendMessage(message, "Я не знаю такой команды! Вы можете перезапустить меня, если что-то пошло не так!", [])
    
    # Primary function
    
    def Get_Shelf_Detail(self, message):
        if (message.text == "Продажи по всем дням в этом месяце"):
            date = datetime.now().strftime('%m')
            query = f"SELECT strftime('%m-%d', s.date) AS day, sh.name AS shelf_name, SUM(s.revenue) AS total_revenue, COUNT(*) AS num_sales FROM sales s JOIN shelves sh ON s.shelf_id = sh.shelf_id WHERE strftime('%m', s.date) = '{date}' GROUP BY day, sh.name ORDER BY day, sh.name;"

            DB = DBController()
            rows = DB.SendQuery(query)
            
            resultString = f'Данные на месяц {date} в формате:\nдень, полка, суммарный доход, число продаж\n\n'
            
            for row in rows:
                resultString += f'{row[0]} - {row[1]} - {row[2]} руб. - {row[3]} шт.\n'
                
            if (self.CheckAllowUsers(message, self.parameters['admins'])):
                self.SendMessage(message, f'{resultString}', self.ButtonsList['AdminMainMenuButtonList'])
            else:
                self.SendMessage(message, f'{resultString}', self.ButtonsList['MainMenuButtonList'])
        
        elif (message.text == "Продажи по всем месяцам в этом году"):
            date = datetime.now().strftime('%Y')
            query = f"SELECT strftime('%Y-%m', s.date) AS month, sh.name AS shelf_name, SUM(s.revenue) AS total_revenue, COUNT(*) AS num_sales FROM sales s JOIN shelves sh ON s.shelf_id = sh.shelf_id WHERE strftime('%Y', s.date) = '{date}' GROUP BY month, sh.name ORDER BY month, sh.name;"
            
            DB = DBController()
            rows = DB.SendQuery(query)
            
            resultString = f'Данные на {date} год в формате:\nмесяц, полка, суммарный доход, число продаж\n\n'
            
            for row in rows:
                resultString += f'{row[0]} - {row[1]} - {row[2]} руб. - {row[3]} шт.\n'
                
            if (self.CheckAllowUsers(message, self.parameters['admins'])):
                self.SendMessage(message, f'{resultString}', self.ButtonsList['AdminMainMenuButtonList'])
            else:
                self.SendMessage(message, f'{resultString}', self.ButtonsList['MainMenuButtonList'])
        elif (message.text == "Продажи за прошлый день"):
            date = (datetime.now() - timedelta(days = 1)).strftime('%Y-%m-%d')
            query = f'SELECT sh.name AS shelf_name, SUM(s.revenue) AS total_revenue, s.date FROM sales s join shelves sh on s.shelf_id = sh.shelf_id WHERE s.date = "{date}" GROUP BY sh.name;'

            DB = DBController()
            rows = DB.SendQuery(query)
            
            resultString = f'Данные на {date}:\n'
            
            if (len(rows) == 0):
                resultString += 'Продаж в этот день нету!'
            else:
                for row in rows:
                    resultString += f'{row[0]} - {row[1]} руб.\n'
                    
            if (self.CheckAllowUsers(message, self.parameters['admins'])):
                self.SendMessage(message, f'{resultString}', self.ButtonsList['AdminMainMenuButtonList'])
            else:
                self.SendMessage(message, f'{resultString}', self.ButtonsList['MainMenuButtonList'])
        elif (message.text == "Средний ежемесячный доход за этот год"):
            date = datetime.now().strftime('%Y')
            query = f"SELECT shelves.name AS shelf_name, AVG(monthly_revenue) AS average_monthly_revenue FROM ( SELECT shelf_id, strftime('%Y-%m', date) AS month, SUM(revenue) AS monthly_revenue FROM sales WHERE strftime('%Y', date) = '{date}' GROUP BY shelf_id, month ) AS monthly_totals JOIN shelves ON monthly_totals.shelf_id = shelves.shelf_id GROUP BY shelves.name;"
            
            DB = DBController()
            rows = DB.SendQuery(query)
            
            resultString = f'В среднем, за месяц в {date} году доход по полкам составил:\n\n'
            totalAverage = 0
            
            for row in rows:
                resultString += f'{row[0]} - {round(row[1], 2)} руб.\n'
                totalAverage += round(row[1], 2)
                
            resultString += f'\nПо всем полкам суммарно: {round(totalAverage, 2)} руб.'
            
            if (self.CheckAllowUsers(message, self.parameters['admins'])):
                self.SendMessage(message, f'{resultString}', self.ButtonsList['AdminMainMenuButtonList'])
            else:
                self.SendMessage(message, f'{resultString}', self.ButtonsList['MainMenuButtonList'])
    
    # Bots function
      
    def SendMessage(self, message, text, buttonList: list | str = None, addStart = True):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        if (buttonList is not None):
            if (type(buttonList) is list):
                for button in buttonList:
                    markup.add(types.KeyboardButton(button))
            else:
                markup.add(types.KeyboardButton(buttonList))
            
            if (addStart):
                markup.add(types.KeyboardButton("/start"))
            
            self.bot.send_message(message.chat.id, text, reply_markup = markup, parse_mode = 'Markdown')
        else:
            self.bot.send_message(message.chat.id, text, parse_mode = 'Markdown')
    
    def CheckAllowUsers(self, message, usersList):
        if (message.chat.id in usersList):
            return True
        
        return False
            
    def Run(self):
        self.bot.polling(none_stop=True, interval=0)