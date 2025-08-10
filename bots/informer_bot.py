import telebot
from telebot import types
import hashlib
import re
import logging
from datetime import datetime, timedelta

from collector.sales_db_controller import DBController
from collector.state_controller import StateController

class InformerBot:
    def __init__(self, parameters: dict, buttonsList: dict):
        self.logger = logging.getLogger('informer_bot')
        
        self.parameters = parameters
        self.ButtonsList = buttonsList
        
        self.StateController = StateController('params/buf_users_state.json')
        
        self.bot = telebot.TeleBot(self.parameters['key'])
        
        self.bot.message_handler(commands=["start"])(self.StartCommand)
        self.bot.message_handler(content_types=["text"])(self.MainFunc)
        
        msg = 'Бот успешно инициирован!'
        print(msg)
        self.logger.info(msg)
        
    def StartCommand(self, message):
        # сообщение об остановке сбора продаж
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
            
        elif (message.text != '') and (self.StateController.GetState(message.chat.id, 'salesCollectState')):
            self.Collect_Sales(message)
            
        elif (message.text == "Начать сбор продаж"):
            self.Begin_Sales_Collect(message)
            
        elif (message.text in self.ButtonsList['DetailShelfButtonList']) and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Get_Shelf_Detail(message)
            
        elif (message.text == "Управление маркетами") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.SendMessage(message, f"Вы хотите добавить маркет?", self.ButtonsList['AdminBeginMarketSalesButtonList'])
            
        elif (message.text == "Ввести код от маркета"):
            self.Begin_Market_Authorization(message)
                
        elif (message.text == "Зарегистрировать новый маркет") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Begin_Add_New_Market(message)
            
        elif (message.text == "Посмотреть актуальные маркеты") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Show_Markets_List(message)
        
        else:
            self.SendMessage(message, "Я не знаю такой команды! Вы можете перезапустить меня, если что-то пошло не так!", [])
    
    # Primary function
    
    def Show_Markets_List(self, message):
        DB = DBController()
        marketsList = DB.GetAllMarkets()
        msg = "Список актуальных маркетов:\n"
        
        for market in marketsList:
            msg += f"{market['name'].capitalize()} ID: {market['market_id']} дата проведения: {market['start_date']} код маркета: `{market['hash']}`\n"
            
        self.SendMessage(message, f"{msg}", self.ButtonsList['AdminMainMenuButtonList'])
        
    
    def Collect_Sales(self, message):
        DB = DBController()
        market = DB.CheckMarketsHash(self.StateController.GetState(message.chat.id, 'selectedMarket'))
        
        try:
            cash = False
            
            if (type(message.text) is str):
                if(message.text.lower()[-1] == 'н'):
                    bufNum = int(message.text.lower().split('н')[0])
                    cash = True
                else:
                    bufNum = int(message.text)
            else:
                bufNum = message.text
                
            # market_id INTEGER, date TEXT, time TEXT, revenue INTEGER, cash TEXT, sender_id, sender_name, FOREIGN KEY(market_id) REFERENCES markets(id)
            if (bufNum > 0):
                buf_sales = {
                    "market_id": market['market_id'],
                    "date": str(datetime.now().strftime('%Y-%m-%d')),
                    "time": str(datetime.now().strftime('%H:%M:%S')),
                    "revenue": bufNum,
                    "cash": cash,
                    "sender_id": str(message.chat.id),
                    "sender_name": str(message.from_user.username)
                }
                lastID = DB.AddMarketsSale(buf_sales)

                if (buf_sales['cash']):
                    msgTypeSales = 'Оплата: Наличные'
                else:
                    msgTypeSales = 'Оплата: Онлайн перевод'
                    
                self.SendMessage(message, f"Продажа зарегистрирована!\nID: {lastID}\nСумма: {buf_sales['revenue']}\n{msgTypeSales}")
            else:
                resultChecking = DB.CheckSalesOwner(bufNum * -1, message.chat.id)
                
                if (resultChecking is not None):
                    if(resultChecking):
                        removedSales = DB.RemoveMarketSaleById(bufNum * -1)
                        self.SendMessage(message, f"Продажа, зарегистрированная в {removedSales['date']} {removedSales['time']}\nc ID: {removedSales['id']}, на сумму {removedSales['revenue']} успешно удалена!")
                    else:
                        self.SendMessage(message, f"У вас нету доступа для удаления данной продажи, так как не вы добавили ее!")
                else:
                    self.SendMessage(message, f"Продажи с ID:{bufNum * -1} не существует!")
        except Exception as e:
            self.SendMessage(message, "Некорректный формат ввода!\nПожалуйста используйте числа и при необходимости обозначить наличный расчет добавляйте букву 'н' после числа!\nПримеры: '300', '450н', '600Н'", [])
        
    def Begin_Sales_Collect(self, message):
        marketHash = self.StateController.GetState(message.chat.id, 'selectedMarket')
        DB = DBController()
        market = DB.CheckMarketsHash(marketHash)
        
        if marketHash:
            self.StateController.ResetAllState(message.chat.id)
            self.StateController.SetUserStats(message.chat.id, 'salesCollectState', True)
            
            self.SendMessage(message, f"Вы успешно запустили сбор данных о продажах для маркета: {market['name']}\nТеперь вы можете писать сумму в чат и она будет автоматически добавятся к списку продаж на маркете!\nЕсли вам нужно прекратить сбор данных, просто напишите команду: /start, или нажмите на кнопку ниже.")
            self.SendMessage(message, 'Все зарегистрированные платежи считаются полученными по переводу. Если необходимо указать, что оплата была произведена наличными добавьте строго после суммы букву заглавную или прописную букву Н.\nНапример так: "600н"\nИли так: "500Н"')
            self.SendMessage(message, f"Каждой продаже присваивается уникальный ID. Если вы хотите удалить какую-либо продажу, напишите боту ID продажи добавив знак - в начале.", [])
        else:
            self.SendMessage(message, "Невозможно внести продажи, так как вы не выбрали маркет!", self.ButtonsList['OfferSelectMarketButtonList'])
    
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
            msg = "Неожиданная ошибка при попытке преобразовать данные о маркете! Обратитесь к администратору!"
            self.SendMessage(message, msg, [])
            
            print(msg + f"{e}")
            self.logger.error(msg + f"{e}")
            
        try:
            DB = DBController()
            DB.AddMarkets(newMarket)
            
        except Exception as e:
            msg = "Ошибка при добавлении маркета в базу данных!"
            
            self.SendMessage(message, msg, [])
            print(msg + f"{e}")
            self.logger.error(msg + f"{e}")
            
        self.StateController.ResetAllState(message.chat.id)
        self.SendMessage(message, f"Вы успешно добавили маркет {newMarket['name']}!\n\nЕго уникальный код: `{newMarket['hash']}`", [])
    
    def Begin_Market_Authorization(self, message):
        self.StateController.ResetAllState(message.chat.id)
        self.StateController.SetUserStats(message.chat.id, 'authorizationState', True)
        
        self.SendMessage(message, "Вам необходимо указать для какого маркета регистрировать продажи. Для этого отправьте уникальный код маркета в чат.\nЕсли необходимо, вы можете перезапустить бота с помощью кнопки start.", [])
        
    def Complete_Market_Authorization(self, message):
        DB = DBController()
        
        market = DB.CheckMarketsHash(str(message.text))
        
        if (market):
            self.StateController.ResetAllState(message.chat.id)
            self.StateController.SetUserStats(message.chat.id, 'selectedMarket', str(message.text))
            self.SendMessage(message, f"Выбран маркет: {market['name']}\nВы можете начать собирать продажи!", self.ButtonsList['CompleteSelectMarketButtonList'])
        else:
            self.SendMessage(message, f"Маркет с кодом: {message.text} не найден! Вы можете попробовать ввести код еще раз:", [])
    
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