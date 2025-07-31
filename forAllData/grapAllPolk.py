import requests
import imapclient
import pyzmail
import re
import json
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from sales_db_controller import DBController
from json_controller import JsonController

parametersDict = {}
try:
    with open('parameters.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
except Exception as e:
    print(f'Ошибка при чтении ссылки! {e}')
    sys.exit(1)

SQL = DBController()
js = JsonController('polk_all_data.json')

# печать результатов
readyLines = []

imap = imapclient.IMAPClient('imap.gmail.com', ssl=True)
imap.login(parametersDict['glogin'], parametersDict['gpass'])
imap.select_folder('INBOX')

sender_email = 'shop@polkius.ru'

query = f'from:{sender_email} has:attachment OR is:important'
uids = imap.search(['X-GM-RAW', query])

readyLines = []

previousDate = datetime.strptime("2000-01-01", '%Y-%m-%d')

for uid in uids:
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
    
    try:
        rows = str(tables[9]).split('</tr>')
        rows = rows[4:-2]
    except Exception as e:
        continue
    
    lastDate = None
    
    for line in rows:
        cleaned_text = re.sub(r'<.*?>', '', line).strip()
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        spitedStr = cleaned_text.split(' ')
        
        if (re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', spitedStr[0])):
            date_obj = datetime.strptime(spitedStr[0], '%d.%m.%Y')
            lastDate = date_obj.strftime('%Y-%m-%d')
            continue
        
        if datetime.strptime(lastDate, '%Y-%m-%d') < previousDate:
            continue
        
        previousDate = datetime.strptime(lastDate, '%Y-%m-%d')
        
        name = ''
        for namePart in spitedStr[0:-4:1]:
            name += namePart + ' '
        
        bufLine = {
            "shelf_id": 1,
            "name": name.strip(),
            "count": int(spitedStr[-2].replace(',000', '')),
            "revenue": int(spitedStr[-1].replace(',', '')),
            "date": lastDate,
            }
        
        readyLines.append(bufLine)
    

imap.logout()
js.writeData(readyLines)