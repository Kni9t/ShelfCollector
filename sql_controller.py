import sqlite3

# Shelf id:
# Polkius - 1
# Wolf - 2
# Fox -3

class SQLController():
    def __init__(self, dbFileName = 'sales.db'):
        self.dbFileName = dbFileName
        self.connection = sqlite3.connect(dbFileName)
        self.cursor = self.connection.cursor()
        
    def CreateTable(self, tableName = 'sales'):
        try:
            cmd = f"CREATE TABLE IF NOT EXISTS shelves (shelf_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
            self.cursor.execute(cmd)
            
            self.cursor.execute("SELECT COUNT(*) FROM shelves;")
            
            if (self.cursor.fetchall()[0][0] < 3):
                self.cursor.execute("INSERT INTO shelves (name) VALUES ('Полкиус');")
                self.cursor.execute("INSERT INTO shelves (name) VALUES ('Волчок');")
                self.cursor.execute("INSERT INTO shelves (name) VALUES ('Лисья полка');")
                self.connection.commit()
            
            self.tableName = tableName
            cmd = f"CREATE TABLE IF NOT EXISTS {tableName} (id INTEGER PRIMARY KEY AUTOINCREMENT, shelf_id INTEGER, name TEXT, count INTEGER, revenue INTEGER, date TEXT, FOREIGN KEY(shelf_id) REFERENCES shelves(id))"
            self.cursor.execute(cmd)
            
            return True, ''
        
        except Exception as e:
            return False, e
        
    def DataInsert(self, dataDict):
        try:
            for line in dataDict:
                cmd = f"INSERT INTO {self.tableName} (shelf_id, name, count, revenue, date) VALUES (?, ?, ?, ?, ?)"
                self.cursor.execute(cmd, (int(line['shelf_id']), str(line['name']), int(line['count']), int(line['revenue']), str(line['date'])))
            
            self.connection.commit()
            return True, ''
            
        except Exception as e:
            return False, e
    
    def SendQuery(self, query):
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        return rows