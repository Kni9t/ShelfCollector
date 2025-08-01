import json

from collector.sales_db_controller import DBController

fileNames = ['wolf_all_data.json', 'fox_all_data.json', 'polk_all_data.json']

resultList = []

for name in fileNames:
    with open(f'ForAllData/{name}', encoding='utf-8') as file:
        resultList = resultList + list(json.load(file))
        file.close()
        
SQL = DBController()

SQL.InitMainTables()

SQL.DataInsert(resultList)