import requests
import imapclient
import pyzmail
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

from jsoncontroller import JsonController

class ShelfCollector:
    def __init__(self, urlPart, gmailLogin, gmailPass):
        self.urlPart = urlPart
        self.gmailLogin = gmailLogin
        self.gmailPass = gmailPass
        self.js = JsonController('buf_shelf_info.txt')
        
        bufData = dict(self.js.getData())
        
        if (bufData == {}):
            bufDate = {
                "polks": "None",
                "fox": "None",
                "wolf": "None"
            }
            self.js.writeData(bufDate)
    
    def CollectSalesPolks(self):
        imap = imapclient.IMAPClient('imap.gmail.com', ssl=True)
        imap.login(self.gmailLogin, self.gmailPass)
        imap.select_folder('INBOX')
        
        sender_email = 'shop@polkius.ru'

        query = f'from:{sender_email} has:attachment OR is:important'
        uids = imap.search(['X-GM-RAW', query])
        
        buids = []
        readyLines = []
        buids.append(uids[-1])
        
        for uid in buids:
            raw_msg = imap.fetch([uid], ['BODY[]'])[uid][b'BODY[]']
            message = pyzmail.PyzMessage.factory(raw_msg)
            
            subject = message.get_subject()
            print(f'Обработка письма: {subject}')

            if not message.html_part:
                print(f'Письмо {uid} не содержит HTML')
                continue

            html = message.html_part.get_payload().decode(message.html_part.charset)
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            
            if not tables:
                print(f'Нет таблиц в письме {uid}')
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
                
                bufLine = {
                    'name': name,
                    'count': int(spitedStr[-2].replace(',000', '')),
                    'revenue': int(spitedStr[-1].replace(',', '')),
                    'date': lastDate,
                }
                
                readyLines.append(bufLine)
            
            bufData = dict(self.js.getData())
            bufData["polks"] = lastDate
            self.js.writeData(bufData)
            
        imap.logout()
        return readyLines
    
    def CollectSalesWolf(self):
        dateFrom = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        dateTo = datetime.now().strftime('%Y-%m-%d')
        
        oldWolfDate = dict(self.js.getData())["wolf"]
            
        if (oldWolfDate == 'None'):
            previousDate = datetime.strptime('2000-01-01', '%Y-%m-%d')
        else:
            previousDate = datetime.strptime(oldWolfDate, '%Y-%m-%d')
            
        if datetime.strptime(dateTo, '%Y-%m-%d') <= previousDate:
            return []

        url = f'{self.urlPart}&dateFrom={dateFrom}&dateTo={dateTo}'

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='table table-bordered', id='rows')

        row = str(table).split('<tr>')
        
        if row[0] == 'None':
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
            
            line = {
                'name': name,
                'count': spitedStr[-3],
                'revenue': spitedStr[-1],
                'date': dateTo,
            }
            
            readyLines.append(line)
        
        bufData = dict(self.js.getData())
        bufData["wolf"] = dateTo
        self.js.writeData(bufData)
        
        return readyLines
    
    def CollectSalesFox(self):
        imap = imapclient.IMAPClient('imap.gmail.com', ssl=True)
        imap.login(self.gmailLogin, self.gmailPass)
        imap.select_folder('INBOX')
        
        sender_email = 'lisyapolka@mail.ru'

        query = f'from:{sender_email} has:attachment OR is:important'
        uids = imap.search(['X-GM-RAW', query])
        
        buids = []
        buids.append(uids[-1])
        
        for uid in buids:
            raw_msg = imap.fetch([uid], ['BODY[]'])[uid][b'BODY[]']
            message = pyzmail.PyzMessage.factory(raw_msg)
            
            subject = message.get_subject()
            print(f'Обработка письма: {subject}')

            if not message.html_part:
                print(f'Письмо {uid} не содержит HTML')
                continue

            html = message.html_part.get_payload().decode(message.html_part.charset)
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            
            if not tables:
                print(f'Нет таблиц в письме {uid}')
                continue
            
            readyLines = []
            
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
                return []
            
            for line in rows:
                cleaned_text = re.sub(r'<.*?>', '', line).strip()
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

                spitedStr = cleaned_text.split(' ')
                
                name = ''
                for namePart in spitedStr[1:-4:1]:
                    name += namePart + ' '
                
                bufLine = {
                    'name': name.strip(),
                    'count': int(spitedStr[-4]),
                    'revenue': int(spitedStr[-1]),
                    'date': lastDate,
                }
                
                readyLines.append(bufLine)
            
            bufData = dict(self.js.getData())
            bufData["fox"] = lastDate
            self.js.writeData(bufData)
            
            imap.logout()
            return readyLines