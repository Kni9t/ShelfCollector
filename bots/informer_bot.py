import telebot
from telebot import types
import hashlib
import re
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
        self.StateController.ResetAllState(message.chat.id)
                
        if (self.CheckAllowUsers(message, self.parameters['admins'])):
            self.SendMessage(message, f'Приветствую, {message.from_user.first_name}! Чем я могу помочь сегодня?', self.ButtonsList['AdminMainMenuButtonList'])
        else:
            self.SendMessage(message, 'Приветствую! Я система по учету продаж на маркетах! Я принадлежу [Hlorkens](https://vk.com/hlorkens)', self.ButtonsList['MainMenuButtonList'])
    
    def MainFunc(self, message):
        if (message.text == "Получить информацию о продажах по полкам") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.SendMessage(message, f"Какую детализацию вы хотели бы получить?", self.ButtonsList['DetailShelfButtonList'])
            
        elif (message.text != '') and (self.StateController.GetState(message.chat.id, 'authorizationState')):
            self.Complete_Market_Authorization(message)
            
        elif (message.text != '') and (self.StateController.GetState(message.chat.id, 'addNewMarket')):
            self.Add_New_Market(message)
            
        elif (message.text in self.ButtonsList['DetailShelfButtonList']) and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Get_Shelf_Detail(message)
            
        elif (message.text == "Начать сбор данных о продажах"):
            if self.CheckAllowUsers(message, self.parameters['admins']):
                self.SendMessage(message, f"Вы хотите добавить маркет?", self.ButtonsList['AdminBeginMarketSalesButtonList'])
            else:
                self.Begin_Market_Authorization(message)
                
        elif (message.text == "Зарегистрировать новый маркет") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Begin_Add_New_Market(message)
        
        elif (message.text == "Выбрать маркет") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Begin_Market_Authorization(message)
        
        else:
            self.SendMessage(message, "Я не знаю такой команды! Вы можете перезапустить меня, если что-то пошло не так!", [])
    
    # Primary function
    
    def Begin_Add_New_Market(self, message):
        self.StateController.ResetAllState(message.chat.id)
        self.StateController.SetUserStats(message.chat.id, 'addNewMarket', True)
        
        self.SendMessage(message, "Введите название маркета и его дату проведения. Формат записи следующий:")
        self.SendMessage(message, "Название маркета <,> дата проведения в формате 2025-07-20-12:00 <,> дата окончания в формате 2025-07-20-12:00")
        self.SendMessage(message, "Пример: `Название маркета, 2025-07-20-12:00, 2025-07-20-12:00`")
    
    def Add_New_Market(self, message):
        data = []
        newMarket = {}
        start_date = ''
        end_date = ''
        
        for dat in message.text.lower().split(','):
            data.append(re.sub(r'\s+', ' ', dat).strip())
        
        try:
            start_date = datetime.strptime(data[1], "%Y-%m-%d-%H:%M")
        except Exception as e:
            self.SendMessage(message, f"Некорректный формат даты начала маркета! Ожидался формат: `2025-07-20-12:00` {e}")
            
        try:
            end_date = datetime.strptime(data[2], "%Y-%m-%d-%H:%M")
        except Exception as e:
            self.SendMessage(message, f"Некорректный формат даты окончания маркета! Ожидался формат: `2025-07-20-12:00` {e}")
        
        try:
            newMarket['hash'] = str(hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:10])
            newMarket['name'] = data[0]
            newMarket['start_date'] = str(start_date.strftime('%Y-%m-%d %H:%M'))
            newMarket['end_date'] = str(end_date.strftime('%Y-%m-%d %H:%M'))
            newMarket['location'] = str(None)
        except Exception as e:
            self.SendMessage(message, f"Неожиданная ошибка при попытке преобразовать данные о маркете! Обратитесь к администратору!")
            self.SendMessage(message, f"{e}", [])
            
        try:
            DB = DBController()
            DB.AddMarkets(newMarket)
            
        except Exception as e:
            msg = "Ошибка при добавлении маркета в базу данных!"
            with open('bot_error_log.txt', 'a', encoding = 'utf-8') as file:
                file.write(msg + f' {e}' + '\n')
                file.close()
            
            self.SendMessage(message, msg, [])
            
        self.StateController.ResetAllState(message.chat.id)        
        self.SendMessage(message, f"Вы успешно добавили маркет {newMarket['name']}!\n\nЕго уникальный код: `{newMarket['hash']}`", [])
    
    def Begin_Market_Authorization(self, message):
        self.StateController.ResetAllState(message.chat.id)
        self.StateController.SetUserStats(message.chat.id, 'authorizationState', True)
        
        self.SendMessage(message, "Хорошо, сперва необходимо указать для какого маркета регистрировать продажи.")
        self.SendMessage(message, "Если необходимо, вы можете перезапустить бота с помощью кнопки start.")
        self.SendMessage(message, "Пожалуйста напишите в чат уникальный ID маркета:", [])
        
    def Complete_Market_Authorization(self, message):
        DB = DBController()
        
        if (DB.CheckMarketsHash(str(message.text))):
            self.StateController.SetUserStats(message.chat.id, 'authorizationState', False)
            self.StateController.SetUserStats(message.chat.id, 'selectedMarket', str(message.text))
            self.SendMessage(message, f"Выбран маркет: {message.text}", [])
        else:
            self.SendMessage(message, f"Маркет: {message.text} не найден!")
    
    def Start_Collect_Market_Sales(self, message):
        pass
    
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