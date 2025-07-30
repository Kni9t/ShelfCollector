import imapclient
import pyzmail
import re
import json
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from openpyxl import load_workbook
from io import BytesIO
import pandas as pd

from sql_controller import SQLController
from json_controller import JsonController

parametersDict = {}
try:
    with open('parameters.json') as file:
        parametersDict = dict(json.load(file))
        file.close()
except Exception as e:
    print(f'Ошибка при чтении ссылки! {e}')
    sys.exit(1)

SQL = SQLController()
js = JsonController('fox_all_data.json')

# печать результатов
readyLines = []

imap = imapclient.IMAPClient('imap.gmail.com', ssl=True)
imap.login(parametersDict['glogin'], parametersDict['gpass'])
imap.select_folder('INBOX')

sender_email = 'lisyapolka@mail.ru'

query = f'from:{sender_email} has:attachment OR is:important'
uids = imap.search(['X-GM-RAW', query])

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
        print(f'Нет таблиц в письме {uid}, обработка .xlsx файла...')
    
        for part in message.mailparts:
            if part.filename and part.filename.endswith('.xlsx'):
                try:
                    xlsx_data = part.get_payload()
                    df = pd.read_excel(BytesIO(xlsx_data), engine='openpyxl', skiprows=5)
                    
                    lastDate = datetime.strptime(list(df['Номенклатура'])[1].split(' ')[0], '%d.%m.%Y').strftime('%Y-%m-%d')
                    
                    for index, row in df.iterrows():
                        string = str(row)
                        
                        string = re.sub(r'Unnamed: [0-9]+', ' ', string).strip()
                        string = re.sub(r'NaN', ' ', string).strip()
                        string = re.sub(r'Цена', ' ', string).strip()
                        string = re.sub(r'dtype: object', ' ', string).strip()
                        string = re.sub(r'Name: [0-9]+,', ' ', string).strip()
                        
                        string = re.sub(r'\s+', ' ', string).strip()
                        
                        string = string.strip()
                        
                        if (re.search(r'\b(\d{2})\.(\d{2})\.(\d{4})\b', string)) or (r'Оксана Александровна' in string):
                            continue
                        
                        if (r'Итого' in string):
                            break
                        
                        splitedStr = string.split(' ')
                        
                        splitedStr.pop(0)
                        splitedStr.pop(0)
                        
                        newStrList = []
                        numbersBuf = []
                        
                        for string in splitedStr[:-4]:
                            newStrList.append(string)
                            
                        for number in splitedStr[:-5:-1]:
                            numberBuf = number.replace(' ', '')
                            numberBuf = numberBuf.replace('.0', '')
                            
                            numbersBuf.append(int(numberBuf))
                        
                        numbersBuf.sort()
                        
                        newStrList.append(numbersBuf.pop(0))
                        
                        numbersBuf = set(numbersBuf)
                        
                        if (len(numbersBuf) == 2):
                            newStrList.append(min(numbersBuf))
                        else:
                            newStrList.append(sorted(numbersBuf)[1])
                        
                        splitedStr = newStrList
                            
                        name = ''
                        for namePart in splitedStr[:-2]:
                            name += namePart + ' '
                            
                        bufLine = {
                            "shelf_id": 3,
                            "name": name.strip(),
                            "count": splitedStr[-2],
                            "revenue": splitedStr[-1],
                            "date": lastDate
                            }
                        
                        readyLines.append(bufLine)
                    
                    print(f'Обработан .xlsx файл: {part.filename}')
                    
                except Exception as e:
                    print(f'Ошибка при обработке Excel: {e}')
    else:
        rows = str(tables[3]).split('</tr>')
        dateRow = rows[4]
        rows = rows[5:-2]
        
        dateRow = re.sub(r'<.*?>', '', dateRow).strip()
        dateRow = re.sub(r'\s+', ' ', dateRow).strip()
        
        lastDate = datetime.strptime(dateRow.split(' ')[0], '%d.%m.%Y').strftime('%Y-%m-%d')
        
        if (datetime.strptime(lastDate, '%Y-%m-%d') < previousDate):
            continue
        
        for line in rows:
            cleaned_text = re.sub(r'<.*?>', '', line).strip()
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

            spitedStr = cleaned_text.split(' ')
            
            name = ''
            for namePart in spitedStr[1:-4:1]:
                name += namePart + ' '

            bufLine = {
                "shelf_id": 3,
                "name": name.strip(),
                "count": int(spitedStr[-4]),
                "revenue": int(spitedStr[-1]),
                "date": lastDate
                }
            
            readyLines.append(bufLine)

imap.logout()
js.writeData(readyLines)
