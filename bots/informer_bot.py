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
        self.logger = logging.getLogger('informer_bot_logger')
        
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
        self.StateController.ResetAllState(message.chat.id)
        marketHash = self.StateController.GetState(message.chat.id, 'selectedMarket')
        
        if (marketHash):
            DB = DBController()
            market = DB.CheckMarketsHash(marketHash)
            
            if (market):
                if (not DB.CheckEndMarket(marketHash)):
                    self.SendMessage(message, f'Вы авторизованы для записи продаж на маркете:\n{market['name']}\nДата проведения: {market['start_date']}')
                else:
                    self.StateController.SetUserStats(message.chat.id, 'selectedMarket', None)
                    self.SendMessage(message, f'Вы авторизованы для маркета: {market['name']}, но он уже не актуален, по этому авторизация для него снята!')
                
        if (self.CheckAllowUsers(message, self.parameters['admins'])):
            self.SendMessage(message, f'Приветствую, {message.from_user.first_name}! Чем я могу помочь сегодня?', self.ButtonsList['AdminMainMenuButtonList'])
        else:
            self.SendMessage(message, 'Приветствую! Я система по учету продаж на маркетах! Я принадлежу [Hlorkens](https://vk.com/hlorkens)', self.ButtonsList['MainMenuButtonList'])
    
    def MainFunc(self, message):
        if (message.text == "Получить информацию о продажах по полкам") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.SendMessage(message, f"Какую детализацию вы хотели бы получить?", self.ButtonsList['DetailShelfButtonList'])
            
        elif (message.text == "Получить информацию о продажах по маркетам") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.SendMessage(message, f"Какую информацию вы хотели бы получить?", self.ButtonsList['DetailMarketButtonList'])
            
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
            
        elif (message.text in self.ButtonsList['DetailMarketButtonList']) and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Get_Markets_Detail(message)
            
        elif (message.text == "Управление маркетами") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.SendMessage(message, f"Вы хотите добавить маркет?", self.ButtonsList['AdminBeginMarketSalesButtonList'])
            
        elif (message.text == "Ввести код от маркета"):
            self.Begin_Market_Authorization(message)
                
        elif (message.text == "Зарегистрировать новый маркет") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Begin_Add_New_Market(message)
            
        elif (message.text == "Посмотреть актуальные маркеты") and self.CheckAllowUsers(message, self.parameters['admins']):
            self.Show_Markets_List(message)
            
        elif (message.text == "Проверить авторизацию"):
            self.ShowCurrentMarket(message)
        
        else:
            self.SendMessage(message, "Я не знаю такой команды! Вы можете перезапустить меня, если что-то пошло не так!", [])
            
            msg = f'Пользователь {message.from_user.username} из чата: {message.chat.id} передал неизвестную команду: [{message.text}]'
            self.logger.warning(msg)
    
    # Primary function
    
    def ShowCurrentMarket(self, message):
        marketHash = self.StateController.GetState(message.chat.id, 'selectedMarket')
        
        if (marketHash):
            DB = DBController()
            market = DB.CheckMarketsHash(marketHash)
            
            if (market):
                marketDescription = f"{market['name'].capitalize()} ID: {market['market_id']}\nДата проведения: {market['start_date']}\nДата окончания: {market['end_date']}\nМесто проведения: {market['location']}\nКод маркета: `{market['hash']}`"
                
                self.SendMessage(message, f'Вы авторизованы для записи продаж на маркете:\n\n{marketDescription}', [])
            else:
                self.SendMessage(message, "Данные по авторизированному маркету отсутствуют в системе, пожалуйста укажите другой код!", self.ButtonsList['OfferSelectMarketButtonList'])
        else:
            self.SendMessage(message, f'Вы не авторизованы для записи продаж на маркете!', self.ButtonsList['OfferSelectMarketButtonList'])
    
    def Show_Markets_List(self, message):
        DB = DBController()
        marketsList = DB.GetAllMarkets()
        if (marketsList):
            msg = "Список актуальных маркетов:\n\n"
            
            for market in marketsList:
                msg += f"{market['name'].capitalize()} ID: {market['market_id']}\nДата проведения: {market['start_date']}\nДата окончания: {market['end_date']}\nМесто проведения: {market['location']}\nКод маркета: `{market['hash']}`\n\n"
            self.SendMessage(message, f"{msg}", self.ButtonsList['AdminMainMenuButtonList'])
        else:
            self.SendMessage(message, "Данные о маркетах отсутствуют в системе!", [])
    
    def Collect_Sales(self, message):
        DB = DBController()
        market = DB.CheckMarketsHash(self.StateController.GetState(message.chat.id, 'selectedMarket'))
        
        if market:
            if (not DB.CheckMarketRunning(self.StateController.GetState(message.chat.id, 'selectedMarket'))):
                self.SendMessage(message, f"Для маркета: {market['name']} можно вносить продажи только в период с {datetime.strptime(market['start_date'], "%Y-%m-%d %H:%M") - timedelta(hours=4)} по {datetime.strptime(market['end_date'], "%Y-%m-%d %H:%M").replace(hour=23, minute=59)}", [])
                return
        else:
            self.SendMessage(message, "Вы авторизированны для маркета, которого нету в базе данных! Пожалуйста, авторизуйтесь для другого маркета!", self.ButtonsList["OfferSelectMarketButtonList"])
            
            msg = f'Пользователь {message.from_user.username} из чата: {message.chat.id} попытался авторизоваться для маркета, однако получить его из БД не удалось [Маркет с таким hash отсутствует в БД!]'
            self.logger.warning(msg)
            return
            
        try:
            cash = False
            inputText = str(message.text).lower()

            if ('н' in inputText):
                cash = True
                inputText = inputText.replace('н', '')
                
            inputText = re.sub(r'\s+', ' ', inputText).strip()
            sum = 0

            for bufSum in inputText.split(' '):
                try:
                    sum += int(bufSum)
                except:
                    self.SendMessage(message, f"Произошла ошибка преобразования значения: {bufSum}! Пожалуйста удалите из него любые символы кроме цифр!")
                    return
                
            # market_id INTEGER, date TEXT, time TEXT, revenue INTEGER, cash TEXT, sender_id, sender_name, FOREIGN KEY(market_id) REFERENCES markets(id)
            if ('-' not in str(message.text)):
                buf_sales = {
                    "market_id": market['market_id'],
                    "date": str(datetime.now().strftime('%Y-%m-%d')),
                    "time": str(datetime.now().strftime('%H:%M:%S')),
                    "revenue": sum,
                    "cash": cash,
                    "sender_id": str(message.chat.id),
                    "sender_name": str(message.from_user.username)
                }
                lastID = DB.AddMarketsSale(buf_sales)

                if (buf_sales['cash']):
                    msgTypeSales = 'Оплата: Наличные'
                else:
                    msgTypeSales = 'Оплата: Онлайн перевод'
                    
                if (lastID is not None):
                    self.SendMessage(message, f"Продажа зарегистрирована!\nID: {lastID}\nСумма: {buf_sales['revenue']}\n{msgTypeSales}")
                
                    msg = f'Пользователь {message.from_user.username} из чата: {message.chat.id} добавил новую продажу для маркета: [{buf_sales}]'
                    self.logger.debug(msg)
                else:
                    self.SendMessage(message, f"Произошла ошибка добавления записи!")
                    self.logger.error(f'Пользователь {message.from_user.username} из чата: {message.chat.id} вызвал ошибку в БД при добавлении: [{buf_sales}]')
            else:
                bufID = 0
                try:
                    pattern = re.compile(r"^-?\d+$")
                    
                    if bool(pattern.fullmatch(str(message.text).strip())):
                        bufID = int(bufSum)
                    else:
                        raise Exception
                except:
                    self.SendMessage(message, f"Обнаружен ID продажи: [{message.text}], но в процессе его преобразования произошла ошибка! Пожалуйста убедитесь, что вы отправили только одно отрицательное число!")
                    return
                
                resultChecking = DB.CheckSalesOwner(bufID * -1, message.chat.id)
                
                if (resultChecking is not None):
                    if(resultChecking):
                        removedSales = DB.RemoveMarketSaleById(bufID * -1)
                        self.SendMessage(message, f"Продажа, зарегистрированная в {removedSales['date']} {removedSales['time']}\nc ID: {removedSales['id']}, на сумму {removedSales['revenue']} успешно удалена!")
                        
                        msg = f'Пользователь {message.from_user.username} из чата: {message.chat.id} удалил продажу для маркета: [{removedSales}]'
                        self.logger.debug(msg)
                    else:
                        self.SendMessage(message, f"У вас нету доступа для удаления данной продажи, так как не вы добавили ее!")
                else:
                    self.SendMessage(message, f"Продажи с ID:{bufID * -1} не существует!")
        except Exception as e:
            self.SendMessage(message, "Произошла ошибка получения значений продажи! Обратитесь к администратору!")
            
            msg = f'У пользователя {message.from_user.username} из чата: {message.chat.id} при введении строки [{message.text}] произошла ошибка: [{e}]'
            self.logger.warning(msg)
        
    def Begin_Sales_Collect(self, message):
        marketHash = self.StateController.GetState(message.chat.id, 'selectedMarket')
        DB = DBController()
        market = DB.CheckMarketsHash(marketHash)
        
        if marketHash:
            if market:
                start_date = datetime.strptime(market['start_date'], "%Y-%m-%d %H:%M") - timedelta(hours=4)
                
                if (DB.CheckMarketRunning(marketHash)):
                    self.StateController.ResetAllState(message.chat.id)
                    self.StateController.SetUserStats(message.chat.id, 'salesCollectState', True)
                    
                    self.SendMessage(message, f"Вы успешно запустили сбор данных о продажах для маркета: {market['name']}\nТеперь вы можете писать сумму в чат и она будет автоматически добавятся к списку продаж на маркете!\nЕсли вам нужно прекратить сбор данных, просто напишите команду: /start, или нажмите на кнопку ниже.")
                    self.SendMessage(message, 'Каждое сообщение соответствует одной продаже на маркете. В сообщении боту вы можете записать ее как одним числом, так и несколькими числами через символ пробела. В случае указания нескольких чисел, бот автоматически просуммирует их в одну итоговую продажу.\nПо умолчанию платежи считаются полученными по переводу. Если необходимо указать, что оплата была произведена наличными добавьте в сообщение заглавную или прописную букву "Н" из русского алфавита.\nПримеры:\nСообщение -> запись у бота\n150 -> 150 руб. переводом\n150н -> 150 руб. наличными\n100 200 -> 300 руб. переводом\n150 300н -> 450 руб. наличными\n-4 -> удалить запись с id -4')
                    self.SendMessage(message, f"Каждой продаже присваивается уникальный ID. Если вы хотите удалить какую-либо продажу, напишите боту ID продажи добавив знак - в начале.", [])
                else:
                    if (start_date >= datetime.now()):
                        self.SendMessage(message, f"Маркет: {market['name']}, еще на начался! Вы сможете начать записывать продажи после: {start_date}", [])
                    else:
                        self.SendMessage(message, f"Маркет: {market['name']}, уже закончился!", [])
            else:
                self.SendMessage(message, "Невозможно внести продажи, так как данные по авторизированному маркету отсутствуют в системе!", self.ButtonsList['OfferSelectMarketButtonList'])
        else:
            self.SendMessage(message, "Невозможно внести продажи, так как вы не выбрали маркет!", self.ButtonsList['OfferSelectMarketButtonList'])
    
    def Begin_Add_New_Market(self, message):
        self.StateController.ResetAllState(message.chat.id)
        self.StateController.SetUserStats(message.chat.id, 'addNewMarket', True)
        
        self.SendMessage(message, "Введите название маркета и его дату проведения. Формат записи следующий:")
        self.SendMessage(message, "Название маркета <,> дата проведения в формате 2025-07-20-12:00 <,> дата окончания в формате 2025-07-20-12:00")
        self.SendMessage(message, "Пример: `Название маркета, 2025-07-20-12:00, 2025-07-20-12:00`", [])
    
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
            self.SendMessage(message, f"Некорректный формат даты начала маркета! Ожидался формат: `2025-07-20-12:00`")
            return
            
        try:
            end_date = datetime.strptime(data[2], "%Y-%m-%d-%H:%M")
        except Exception as e:
            self.SendMessage(message, f"Некорректный формат даты окончания маркета! Ожидался формат: `2025-07-20-12:00`")
            return
        
        try:
            location = ''
            for st in data[3:]:
                location += st + ' '

            data = data[:3]
            
            if (location != ''):
                data.append(location.strip())
            else:
                data.append(str(None))
        except Exception as e:
            msg = "Не удалось преобразовать адрес! Попробуйте удалить спец символы из адреса или обратитесь к администратору!"
            
            self.SendMessage(message, msg)
            self.logger.warning(msg + f" [{e}]")
            return
        
        try:
            newMarket['hash'] = str(hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:10])
            newMarket['name'] = data[0]
            newMarket['start_date'] = str(start_date.strftime('%Y-%m-%d %H:%M'))
            newMarket['end_date'] = str(end_date.strftime('%Y-%m-%d %H:%M'))
            newMarket['location'] = data[3]
        except Exception as e:
            msg = "Неожиданная ошибка при попытке преобразовать данные о маркете! Обратитесь к администратору!"
            self.SendMessage(message, msg, [])
            
            self.logger.error(msg + f" [{e}]")
            return
            
        DB = DBController()
        result = DB.AddMarkets(newMarket)
        
        if (result is None):
            msg = "Ошибка при добавлении маркета в базу данных! Обратитесь к администратору!"
        
            self.SendMessage(message, msg, [])
            self.logger.error(msg)
            return
        else:
            self.StateController.ResetAllState(message.chat.id)
            self.SendMessage(message, f"Вы успешно добавили маркет: {newMarket['name'].capitalize()}!\n\nЕго уникальный код: `{newMarket['hash']}`", [])
            
            msg = f'Пользователь {message.from_user.username} из чата: {message.chat.id} добавил новый маркет: [{newMarket}]'
            self.logger.debug(msg)
    
    def Begin_Market_Authorization(self, message):
        self.StateController.ResetAllState(message.chat.id)
        self.StateController.SetUserStats(message.chat.id, 'authorizationState', True)
        
        self.SendMessage(message, "Вам необходимо указать для какого маркета регистрировать продажи. Для этого отправьте уникальный код маркета в чат.\nЕсли необходимо, вы можете перезапустить бота с помощью кнопки start.", [])
        
    def Complete_Market_Authorization(self, message):
        DB = DBController()
        
        market = DB.CheckMarketsHash(str(message.text))
        
        if (market):
            if (not DB.CheckEndMarket(str(message.text))):
                self.StateController.ResetAllState(message.chat.id)
                self.StateController.SetUserStats(message.chat.id, 'selectedMarket', str(message.text))
                
                start_date = datetime.strptime(market['start_date'], "%Y-%m-%d %H:%M") - timedelta(hours=4)
                
                self.SendMessage(message, f"Выбран маркет: {market['name']}\nВы можете начать собирать продажи c {start_date}!", self.ButtonsList['CompleteSelectMarketButtonList'])
                
                msg = f'Пользователь {message.from_user.username} из чата: {message.chat.id} успешно авторизовался для маркета: [{market}]'
                self.logger.debug(msg)
            else:
                self.SendMessage(message, f"Данный маркет уже закончился!", [])
        else:
            self.SendMessage(message, f"Маркет с кодом: {message.text} не найден! Вы можете попробовать ввести код еще раз или же сбросить ввод кода и нажать /start!", [])
    
    def Get_Markets_Detail(self, message):
        DB = DBController()
        
        # Добавить в DetailMarketButtonList
        # "Доход по маркетам в прошлом месяце",
        # "Средний ежемесячный доход с маркетов за этот год",
        
        if (message.text == "Доход по маркетам в прошлом месяце"):
            self.SendMessage(message, 'Пока данный функционал отсутствует!', [])
        
        elif (message.text == "Средний ежемесячный доход с маркетов за этот год"):
            self.SendMessage(message, 'Пока данный функционал отсутствует!', [])
        
        elif (message.text == "Доход со всех маркетов"):
            salesList = DB.GetAllMarketSales()
            
            if (salesList):
                msg = ''
                for market in salesList:
                    msg += f'{market['name']}\n{market['date']}\nНаличные: {market['cash']} руб.\nПереводы: {market['online']} руб.\nИтог: {market['total']} руб.\n\n'
            
                self.SendMessage(message, f"{msg}", [])
            else:
                self.SendMessage(message, "Данные о маркетах отсутствуют в системе!", [])
      
    def Get_Shelf_Detail(self, message):
        if (message.text == "Продажи по всем дням в этом месяце"):
            date = datetime.now().strftime('%m')
            query = f"SELECT strftime('%m-%d', s.date) AS day, sh.name AS shelf_name, SUM(s.revenue) AS total_revenue, COUNT(*) AS num_sales FROM sales s JOIN shelves sh ON s.shelf_id = sh.shelf_id WHERE strftime('%m', s.date) = '{date}' GROUP BY day, sh.name ORDER BY day, sh.name;"

            DB = DBController()
            rows = DB.SendQuery(query)
            
            if (rows):
                resultString = f'Данные на месяц {date} в формате:\nдень, полка, суммарный доход, число продаж\n\n'
            
                for row in rows:
                    resultString += f'{row[0]} - {row[1]} - {row[2]} руб. - {row[3]} шт.\n'
                    
                self.SendMessage(message, f'{resultString}', self.ButtonsList['AdminMainMenuButtonList'])
            else:
                self.SendMessage(message, "Данные о полках отсутствуют в системе!", [])
        
        elif (message.text == "Продажи по всем месяцам в этом году"):
            date = datetime.now().strftime('%Y')
            query = f"SELECT strftime('%Y-%m', s.date) AS month, sh.name AS shelf_name, SUM(s.revenue) AS total_revenue, COUNT(*) AS num_sales FROM sales s JOIN shelves sh ON s.shelf_id = sh.shelf_id WHERE strftime('%Y', s.date) = '{date}' GROUP BY month, sh.name ORDER BY month, sh.name;"
            
            DB = DBController()
            rows = DB.SendQuery(query)
            
            if (rows):
                resultString = f'Данные на {date} год в формате:\nмесяц, полка, суммарный доход, число продаж\n\n'
            
                for row in rows:
                    resultString += f'{row[0]} - {row[1]} - {row[2]} руб. - {row[3]} шт.\n'
                    
                self.SendMessage(message, f'{resultString}', self.ButtonsList['AdminMainMenuButtonList'])
            else:
                self.SendMessage(message, "Данные о полках отсутствуют в системе!", [])
            
        elif (message.text == "Продажи за прошлый день"):
            date = (datetime.now() - timedelta(days = 1)).strftime('%Y-%m-%d')
            query = f'SELECT sh.name AS shelf_name, SUM(s.revenue) AS total_revenue, s.date FROM sales s join shelves sh on s.shelf_id = sh.shelf_id WHERE s.date = "{date}" GROUP BY sh.name;'

            DB = DBController()
            rows = DB.SendQuery(query)
            
            if (rows):
                resultString = f'Данные на {date}:\n'
            
                if (len(rows) == 0):
                    resultString += 'Продаж в этот день нету!'
                else:
                    for row in rows:
                        resultString += f'{row[0]} - {row[1]} руб.\n'
                        
                self.SendMessage(message, f'{resultString}', self.ButtonsList['AdminMainMenuButtonList'])
            else:
                self.SendMessage(message, "Данные о полках отсутствуют в системе!", [])
            
        elif (message.text == "Средний ежемесячный доход за этот год"):
            date = datetime.now().strftime('%Y')
            query = f"SELECT shelves.name AS shelf_name, AVG(monthly_revenue) AS average_monthly_revenue FROM ( SELECT shelf_id, strftime('%Y-%m', date) AS month, SUM(revenue) AS monthly_revenue FROM sales WHERE strftime('%Y', date) = '{date}' GROUP BY shelf_id, month ) AS monthly_totals JOIN shelves ON monthly_totals.shelf_id = shelves.shelf_id GROUP BY shelves.name;"
            
            DB = DBController()
            rows = DB.SendQuery(query)
            
            if (rows):
                resultString = f'В среднем, за месяц в {date} году доход по полкам составил:\n\n'
                totalAverage = 0
                
                for row in rows:
                    resultString += f'{row[0]} - {round(row[1], 2)} руб.\n'
                    totalAverage += round(row[1], 2)
                    
                resultString += f'\nПо всем полкам суммарно: {round(totalAverage, 2)} руб.'
                
                self.SendMessage(message, f'{resultString}', self.ButtonsList['AdminMainMenuButtonList'])
            else:
                self.SendMessage(message, "Данные о полках отсутствуют в системе!", [])
    
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