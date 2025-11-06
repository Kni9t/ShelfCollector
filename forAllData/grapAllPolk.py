import requests
import imapclient
import pyzmail
import re
import json
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from collector.sales_db_controller import DBController
from collector.json_controller import JsonController

parametersDict = {}
try:
    with open('params/parameters.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
except Exception as e:
    print(f'Ошибка при чтении ссылки! {e}')
    sys.exit(1)

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
        print(f'Письмо {subject} не содержит HTML')
        continue

    html = message.html_part.get_payload().decode(message.html_part.charset)
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    
    if not tables:
        print(f'Нет таблиц в письме {subject}')
        continue
    
    try:
        rows = str(tables[9]).split('</tr>')
        rows = rows[4:-2]
    except Exception as e:
        print(f'Ошибка при обработке письма {subject}')
        continue
    
    for line in rows:
        spitedStr = line.split('\n')
        clearStrings = []
        
        for bufStr in spitedStr:
            bufStr = re.sub(r'<.*?>', '', bufStr).strip()
            bufStr = re.sub(r'\s+', ' ', bufStr).strip()
            if (bufStr != ''):
                clearStrings.append(bufStr)
                
        if (re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', clearStrings[0])):
            lastFoundDate = datetime.strptime(clearStrings[0], '%d.%m.%Y').strftime('%Y-%m-%d')
            print(f'Обнаружена новая дата: {lastFoundDate}')
            continue
        
        if datetime.strptime(lastFoundDate, '%Y-%m-%d') <= previousDate:
            continue

        bufLine = {
            "shelf_id": 1,
            "name": clearStrings[0].strip(),
            "count": int(clearStrings[-2].replace(',000', '').strip()),
            "revenue": float(clearStrings[-1].replace(' ', '').replace(',', '.').strip()),
            "date": lastFoundDate,
            }
        
        readyLines.append(bufLine)
        print(bufLine)
        
    if (lastFoundDate is not None):
        previousDate = datetime.strptime(lastFoundDate, '%Y-%m-%d')

imap.logout()
js.writeData(readyLines)