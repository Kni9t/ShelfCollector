import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re

class ShelfCollector:
    def __init__(self, urlPart):
        self.urlPart = urlPart
    
    def CollectSales(self):
        dateFrom = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        dateTo = datetime.now().strftime('%Y-%m-%d')

        url = f'{self.urlPart}&dateFrom={dateFrom}&dateTo={dateTo}'

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='table table-bordered', id='rows')

        row = str(table).split('<tr>')
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
                'price': spitedStr[-2],
                'revenue': spitedStr[-1],
                'date': dateTo,
            }
            
            readyLines.append(line)
            
        return readyLines