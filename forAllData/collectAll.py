import json

from sql_controller import SQLController

fileNames = ['wolf_all_data.json', 'fox_all_data.json', 'polk_all_data.json']

resultList = []

for name in fileNames:
    with open(f'ForAllData/{name}', encoding='utf-8') as file:
        resultList = resultList + list(json.load(file))
        file.close()
        
SQL = SQLController()

SQL.CreateTable()

SQL.DataInsert(resultList)