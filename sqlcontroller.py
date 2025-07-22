import sqlite3

class SQLController():
    def __init__(self, dbFileName = 'sales.db'):
        self.dbFileName = dbFileName
        self.connection = sqlite3.connect(dbFileName)
        self.cursor = self.connection.cursor()
        
    def CreateTable(self, tableName = 'sales'):
        try:
            self.tableName = tableName
            cmd = f"CREATE TABLE IF NOT EXISTS {tableName} (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, count INTEGER, revenue INTEGER, date TEXT)"
            self.cursor.execute(cmd)
            
            return True, ''
        
        except Exception as e:
            return False, e
        
    def DataInsert(self, dataDict):
        try:
            for line in dataDict:
                cmd = f"INSERT INTO {self.tableName} (name, count, revenue, date) VALUES (?, ?, ?, ?)"
                self.cursor.execute(cmd, (str(line['name']), int(line['count']), int(line['revenue']), str(line['date'])))
            
            self.connection.commit()
            return True, ''
            
        except Exception as e:
            return False, e