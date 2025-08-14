import requests
import imapclient
import pyzmail
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
import logging

from collector.json_controller import JsonController

class ShelfCollector:
    def __init__(self, urlPart, gmailLogin, gmailPass):
        self.urlPart = urlPart
        self.gmailLogin = gmailLogin
        self.gmailPass = gmailPass
        self.js = JsonController('params/buf_shelf_info.json')
        
        self.logger = logging.getLogger('shelf_logger')
        
        bufData = dict(self.js.getData())
        
        if (bufData == {}):
            bufDate = {
                "polks": "None",
                "fox": "None",
                "wolf": "None"
            }
            self.js.writeData(bufDate)
    
    def CollectSalesPolks(self):
        try:
            sender_email = 'shop@polkius.ru'
            
            mails = self._GetMessagesFromGmail(sender_email, 1)
            
            readyLines = []
            
            lastDate = None
            
            for mail in mails:
                title = mail.get_subject()
                
                msg = f'Обработка письма: {title}'
                
                print(msg)
                self.logger.debug(msg)
                
                if not mail.html_part:
                    msg = f'Письмо: {title} не содержит HTML'
                    
                    print(msg)
                    self.logger.debug(msg)
                    continue
                
                html = mail.html_part.get_payload().decode(mail.html_part.charset)
                soup = BeautifulSoup(html, 'html.parser')
                tables = soup.find_all('table')
                
                if not tables:
                    msg = f'Нет таблиц в письме: {title}'
                    
                    print(msg)
                    self.logger.warning(msg)
                    continue
                
                rows = str(tables[9]).split('</tr>')
                rows = rows[4:-2]
                
                oldPolksDate = dict(self.js.getData())["polks"]
                
                if (oldPolksDate == 'None'):
                    previousDate = datetime.strptime('2000-01-01', '%Y-%m-%d')
                else:
                    previousDate = datetime.strptime(oldPolksDate, '%Y-%m-%d')
                    
                lastDate = None
                
                for line in rows:
                    cleaned_text = re.sub(r'<.*?>', '', line).strip()
                    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                    
                    spitedStr = cleaned_text.split(' ')
                    
                    if (re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', spitedStr[0])):
                        date_obj = datetime.strptime(spitedStr[0], '%d.%m.%Y')
                        lastDate = date_obj.strftime('%Y-%m-%d')
                        continue
                    
                    if datetime.strptime(lastDate, '%Y-%m-%d') <= previousDate:
                        continue
                    
                    name = ''
                    for namePart in spitedStr[0:-4:1]:
                        name += namePart + ' '
                    
                    bufLine = self._createDict(
                        shelf_id = 1,
                        name = name,
                        count = spitedStr[-2].replace(',000', ''),
                        revenue = spitedStr[-1].replace(',', ''),
                        date = lastDate,
                    )
                    
                    readyLines.append(bufLine)
                
                if (len(readyLines) == 0):
                    msg = f'Данные из письма: {title} уже содержатся в БД!'
                    
                    print(msg)
                    self.logger.debug(msg)
                else:
                    msg = f'Письмо: {title} обработано успешно!'
                    
                    print(msg)
                    self.logger.info(msg)
                    
            bufData = dict(self.js.getData())
            
            if (lastDate is not None):
                bufData["polks"] = lastDate
                self.js.writeData(bufData)
                
            return readyLines
        except Exception as e:
            msg = f'При сборе данных с Полкиуса произошла ошибка! [{e}]'
                    
            print(msg)
            self.logger.error(msg)
    
    def CollectSalesFox(self):
        try:
            sender_email = 'lisyapolka@mail.ru'
            
            mails = self._GetMessagesFromGmail(sender_email, 1)
            
            readyLines = []
            
            lastDate = None
            
            for mail in mails:
                title = mail.get_subject()
                
                msg = f'Обработка письма: {title}'
                
                print(msg)
                self.logger.debug(msg)
                
                if not mail.html_part:
                    msg = f'Письмо: {title} не содержит HTML'
                    
                    print(msg)
                    self.logger.debug(msg)
                    continue
                
                html = mail.html_part.get_payload().decode(mail.html_part.charset)
                soup = BeautifulSoup(html, 'html.parser')
                tables = soup.find_all('table')
                
                if not tables:
                    msg = f'Нет таблиц в письме: {title}'
                    
                    print(msg)
                    self.logger.warning(msg)
                    continue
                
                rows = str(tables[3]).split('</tr>')
                dateRow = rows[4]
                rows = rows[5:-2]
                
                dateRow = re.sub(r'<.*?>', '', dateRow).strip()
                dateRow = re.sub(r'\s+', ' ', dateRow).strip()
                
                lastDate = datetime.strptime(dateRow.split(' ')[0], '%d.%m.%Y').strftime('%Y-%m-%d')
                
                oldFoxDate = dict(self.js.getData())["fox"]
                
                if (oldFoxDate == 'None'):
                    previousDate = datetime.strptime('2000-01-01', '%Y-%m-%d')
                else:
                    previousDate = datetime.strptime(oldFoxDate, '%Y-%m-%d')
                
                if (datetime.strptime(lastDate, '%Y-%m-%d') <= previousDate):
                    msg = f'Данные из письма: {title} уже содержатся в БД!'
                    
                    print(msg)
                    self.logger.debug(msg)
                    continue
                
                for line in rows:
                    cleaned_text = re.sub(r'<.*?>', '', line).strip()
                    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

                    spitedStr = cleaned_text.split(' ')
                    
                    name = ''
                    for namePart in spitedStr[1:-4:1]:
                        name += namePart + ' '
                    
                    bufLine = self._createDict(
                        shelf_id = 3,
                        name = name,
                        count = spitedStr[-4],
                        revenue = spitedStr[-1],
                        date = lastDate,
                    )
                    
                    readyLines.append(bufLine)
                    
                msg = f'Письмо: {title} успешно обработано!'
                
                print(msg)
                self.logger.info(msg)
            
            bufData = dict(self.js.getData())
            
            if (lastDate is not None):
                bufData["fox"] = lastDate
                self.js.writeData(bufData)
            
            return readyLines
        
        except Exception as e:
            msg = f'При сборе данных с Лисьей полки произошла ошибка! [{e}]'
                    
            print(msg)
            self.logger.error(msg)
    
    def CollectSalesWolf(self):
        try:
            dateTo = (datetime.now() - timedelta(days = 1)).strftime('%Y-%m-%d')
            
            msg = f'Обработка сайта: Волчок {dateTo}'
                
            print(msg)
            self.logger.debug(msg)
            
            oldWolfDate = dict(self.js.getData())["wolf"]
                
            if (oldWolfDate == 'None'):
                previousDate = datetime.strptime('2000-01-01', '%Y-%m-%d')
            else:
                previousDate = datetime.strptime(oldWolfDate, '%Y-%m-%d')
                
            if datetime.strptime(dateTo, '%Y-%m-%d') <= previousDate:
                msg = f'Данные с сайта Волчок за {dateTo} уже содержатся в БД!'
                
                print(msg)
                self.logger.debug(msg)
                return []

            url = f'{self.urlPart}&dateFrom={dateTo}&dateTo={dateTo}'

            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', class_='table table-bordered', id='rows')

            row = str(table).split('<tr>')
            
            if row[0] == 'None':
                msg = f'Продажи у Волчока за {dateTo} отсутствуют!'
                
                print(msg)
                self.logger.warning(msg)
                return []
            
            row.pop(0)
            row.pop(0)
            row.pop(-1)
            
            readyLines = []

            for line in row:
                cleaned_text = re.sub(r'<.*?>', '', line).strip()
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                
                spitedStr = cleaned_text.split(' ')
                
                spitedStr.pop(0)
                spitedStr.pop(0)
                
                name = ''
                for namePart in spitedStr[0:-3:1]:
                    name += namePart + ' '
                
                bufLine = self._createDict(
                    shelf_id = 2,
                    name = name,
                    count = spitedStr[-3],
                    revenue = spitedStr[-1],
                    date = dateTo,
                    )
                
                readyLines.append(bufLine)
                
            msg = f'Данные с сайта Волчок за {dateTo} успешно собраны!'
            
            print(msg)
            self.logger.debug(msg)
            
            bufData = dict(self.js.getData())
            bufData["wolf"] = dateTo
            self.js.writeData(bufData)
            
            return readyLines
        
        except Exception as e:
            msg = f'При сборе данных с Волчка произошла ошибка! [{e}]'
                    
            print(msg)
            self.logger.error(msg)
    
    def _createDict(self, shelf_id, name, count, revenue, date):
        bufLine = {
                    "shelf_id": shelf_id,
                    "name": name.strip(),
                    "count": int(count),
                    "revenue": int(revenue),
                    "date": date,
                }
        return bufLine
    
    def _GetMessagesFromGmail(self, email, count = 0):
        try:
            imap = imapclient.IMAPClient('imap.gmail.com', ssl=True)
            imap.login(self.gmailLogin, self.gmailPass)
            imap.select_folder('INBOX')
            
            query = f'from:{email} has:attachment OR is:important'
            uids = imap.search(['X-GM-RAW', query])
            
            uids.reverse()
            
            messageList = []
            
            if (count > 0):
                uids = uids[:count]
            
            for uid in uids:
                raw_msg = imap.fetch([uid], ['BODY[]'])[uid][b'BODY[]']
                message = pyzmail.PyzMessage.factory(raw_msg)
                
                messageList.append(message)
                
            imap.logout()
            return messageList
        
        except Exception as e:
            msg = f'Ошибка при получении письма из gmail! [{e}]'
            print(msg)
            self.logger.info(msg)