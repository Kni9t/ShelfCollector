import requests
import imapclient
import pyzmail
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import sys

from collector.sales_db_controller import DBController
from collector.json_controller import JsonController

js = JsonController('wolf_all_data.json')

end_date = datetime.now()
start_date = end_date - timedelta(days=180)

ranges = []

current_date = start_date
while current_date < end_date:
    next_date = current_date + timedelta(days=1)
    ranges.append((current_date.strftime('%Y-%m-%d'), next_date.strftime('%Y-%m-%d')))
    current_date = next_date

# печать результатов
readyLines = []

for d_from, d_to in ranges:
    print(f'Обработка сайта: Волчок c {d_to} до {d_to}')

    url = f'https://d-o-k.ru/47740f?supplier=2fe77177-3b2e-11f0-0a80-0457000121bd&bundle_id=161&dateFrom={d_to}&dateTo={d_to}'

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_='table table-bordered', id='rows')

    row = str(table).split('<tr>')

    if row[0] == 'None':
        continue

    row.pop(0)
    row.pop(0)
    row.pop(-1)

    for line in row:
        cleaned_text = re.sub(r'<.*?>', '', line).strip()
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        spitedStr = cleaned_text.split(' ')
        
        spitedStr.pop(0)
        spitedStr.pop(0)
        
        name = ''
        for namePart in spitedStr[0:-4:1]:
            name += namePart + ' '
        
        line = {
            "shelf_id": 2,
            "name": name.strip(),
            "count": int(spitedStr[-4]),
            "revenue": float(spitedStr[-1].replace(',', '.')),
            "date": d_to,
        }
        print(line)
        
        readyLines.append(line)

js.writeData(readyLines)