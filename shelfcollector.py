import requests
import imapclient
import pyzmail
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

class ShelfCollector:
    def __init__(self, urlPart, gmailLogin, gmailPass):
        self.urlPart = urlPart
        self.gmailLogin = gmailLogin
        self.gmailPass = gmailPass
    
    def CollectSales(self, sender_email):
        imap = imapclient.IMAPClient('imap.gmail.com', ssl=True)
        imap.login(self.gmailLogin, self.gmailPass)
        imap.select_folder('INBOX')

        query = f'from:{sender_email} has:attachment OR is:important'
        uids = imap.search(['X-GM-RAW', query])
        
        buids = []
        readyLines = []
        buids.append(uids[-1])
        
        for uid in buids:
            raw_msg = imap.fetch([uid], ['BODY[]'])[uid][b'BODY[]']
            message = pyzmail.PyzMessage.factory(raw_msg)
            
            subject = message.get_subject()
            print(f'Заголовок письма {uid}: {subject}')

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
            
            lastDate = None
            
            for line in rows:
                cleaned_text = re.sub(r'<.*?>', '', line).strip()
                cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
                
                spitedStr = cleaned_text.split(' ')
                
                if (re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', spitedStr[0])):
                    date_obj = datetime.strptime(spitedStr[0], '%d.%m.%Y')
                    lastDate = date_obj.strftime('%Y-%m-%d')
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
            
        imap.logout()
        return readyLines
    
    def CollectSalesWolf(self):
        dateFrom = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        dateTo = datetime.now().strftime('%Y-%m-%d')

        url = f'{self.urlPart}&dateFrom={dateFrom}&dateTo={dateTo}'

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='table table-bordered', id='rows')

        row = str(table).split('<tr>')
        
        if len(row) == 0:
            return {}
        
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
            
        return readyLines