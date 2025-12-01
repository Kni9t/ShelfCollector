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
            
    def GetSales(self, email):
        full_mail = self._GetMailContent(email, 1)[0]
        mail_payload = full_mail.html_part.get_payload().decode(full_mail.html_part.charset)
        
        soup = BeautifulSoup(mail_payload, 'html.parser')
        tables = soup.find_all('table')
        
        trList = []
        tdList = []
        resultList = []
        
        # Find first table with <tr> tag with class R7
        for tab in tables:
            buf = tab.find_all('tr', class_="R7")
            if buf:
                if (len(buf) > 0):
                    trList = buf
                    break
        
        # Find four <td> tags in each <tr>
        for tr in trList:
            buf = tr.find_all('td', limit = 4)
            if buf:
                if (len(buf) > 0):
                    tdList.append(buf)
                    
        # Format text
        for block in tdList:
            buf = []
            count = 0
            for td in block:
                text = td.string
                if text:
                    text = text.strip()
                    text = text.replace(u'\xa0', '')
                    
                    match count:
                        case 0:
                            if ('Оксана' in text):
                                break
                            bufDate = self._formatDate(text)
                            if (bufDate):
                                text = bufDate
                                buf.append(text)
                                break
                        case 1:
                            pass
                        case 2:
                            pass
                        case 3:
                            pass
                    
                    text = text.replace(',000', '')
                    buf.append(text)
                else:
                    buf.append(text)
                count += 1
            if (len(buf) > 0):
                resultList.append(buf)

        tables = resultList
        
        with open(email, "w", encoding='utf8') as outfile:
            outfile.write(str(tables))
            outfile.close()
    
    def CollectSalesPolks(self):
        try:
            sender_email = 'shop@polkius.ru'
            
            mails = self._GetMailContent(sender_email, 1)
            
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
                
                if (len(tables) < 9):
                    msg = f'Нет таблицы с данными о продажах в письме: {title}'
                    
                    print(msg)
                    self.logger.warning(msg)
                    continue
                
                rows = str(tables[9]).split('</tr>')
                rows = rows[4:-2]
                
                oldPolksDate = dict(self.js.getData())["polks"]
                
                if (str(oldPolksDate) == 'None'):
                    previousDate = datetime.strptime('2000-01-01', '%Y-%m-%d')
                else:
                    previousDate = datetime.strptime(oldPolksDate, '%Y-%m-%d')
                    
                lastDate = None
                
                for line in rows:
                    spitedStr = line.split('\n')
                    clearStrings = []
                    
                    for bufStr in spitedStr:
                        bufStr = re.sub(r'<.*?>', '', bufStr).strip()
                        bufStr = re.sub(r'\s+', ' ', bufStr).strip()
                        if (bufStr != ''):
                            clearStrings.append(bufStr)
                            
                    if (re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', clearStrings[0])):
                        date_obj = datetime.strptime(clearStrings[0], '%d.%m.%Y')
                        lastDate = date_obj.strftime('%Y-%m-%d')
                        continue
                    
                    if datetime.strptime(lastDate, '%Y-%m-%d') <= previousDate:
                        continue
                        
                    bufLine = self._createDict(
                        shelf_id = 1,
                        name = clearStrings[0],
                        count = clearStrings[-2].replace(',000', '').strip(),
                        revenue = clearStrings[-1].replace(' ', '').strip(),
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
            
            mails = self._GetMailContent(sender_email, 1)
            
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
                
                if (str(oldFoxDate) == 'None'):
                    previousDate = datetime.strptime('2000-01-01', '%Y-%m-%d')
                else:
                    previousDate = datetime.strptime(oldFoxDate, '%Y-%m-%d')
                
                if (datetime.strptime(lastDate, '%Y-%m-%d') <= previousDate):
                    msg = f'Данные из письма: {title} уже содержатся в БД!'
                    
                    print(msg)
                    self.logger.debug(msg)
                    continue
                
                for line in rows:
                    lineList = []
                    if ('<td class="R8C1">' in line):
                        contentLine = line.split('<td class="R8C1">')
                    elif ('<td class="R9C1">' in line):
                        contentLine = line.split('<td class="R9C1">')
                    
                    for content in contentLine:
                        content = re.sub(r'<.*?>', '', content).strip()
                        content = re.sub(r'\s+', ' ', content).strip()
                        lineList.append(content)
                    
                    bufLine = self._createDict(
                        shelf_id = 3,
                        name = re.sub(r'^\d+(?:\.\d+)*\.\s*', '', lineList[0]),
                        count = re.sub(r'\s+', '', lineList[1]).strip(),
                        revenue = re.sub(r'\s+', '', lineList[-1]).strip(),
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
                
            if (str(oldWolfDate) == "None"):
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
    
    def _formatDate(self, dateStr):
        resultDate = None
        
        if re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', dateStr):
            try:
                resultDate = datetime.strptime(dateStr, '%d.%m.%Y').strftime('%Y-%m-%d')
                
            except Exception as e:
                resultDate = datetime.strptime(dateStr, '%d.%m.%Y %H:%M:%S').strftime('%Y-%m-%d')
                # print('Ошибка') TODO?
        return resultDate
    
    def _createDict(self, shelf_id, name, count, revenue, date):
        bufLine = {
                    "shelf_id": shelf_id,
                    "name": name.strip(),
                    "count": int(float(count.replace(',', '.'))) if isinstance(count, str) else int(float(count)),
                    "revenue": float(revenue.replace(',', '.')) if isinstance(revenue, str) else float(revenue),
                    "date": date,
                }
        return bufLine
    
    def _GetMailContent(self, email, count = 0):
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