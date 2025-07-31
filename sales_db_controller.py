import sqlite3

# Shelf id:
# Polkius - 1
# Wolf - 2
# Fox -3

class DBController():
    def __init__(self, dbFileName = 'sales.db'):
        self.dbFileName = dbFileName
        self.connection = sqlite3.connect(dbFileName)
        self.cursor = self.connection.cursor()
        
    def InitMainTables(self):
        cmd = f"CREATE TABLE IF NOT EXISTS shelves (shelf_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
        self.cursor.execute(cmd)
        
        self.cursor.execute("SELECT COUNT(*) FROM shelves;")
        
        if (self.cursor.fetchall()[0][0] < 3):
            self.cursor.execute("INSERT INTO shelves (name) VALUES ('Полкиус');")
            self.cursor.execute("INSERT INTO shelves (name) VALUES ('Волчок');")
            self.cursor.execute("INSERT INTO shelves (name) VALUES ('Лисья полка');")
            self.connection.commit()
            
        cmd = f"CREATE TABLE IF NOT EXISTS markets (market_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, start_date TEXT, end_date TEXT, location TEXT)"
        self.cursor.execute(cmd)
        
        cmd = f"CREATE TABLE IF NOT EXISTS market_sales (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, time TEXT, end_date TEXT, revenue INTEGER, cash TEXT, sender_id, sender_name)"
        self.cursor.execute(cmd)
        
        cmd = f"CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, shelf_id INTEGER, name TEXT, count INTEGER, revenue INTEGER, date TEXT, FOREIGN KEY(shelf_id) REFERENCES shelves(id))"
        self.cursor.execute(cmd)
        
    def AddShelfSale(self, dataDict):
        for line in dataDict:
            cmd = f"INSERT INTO sales (shelf_id, name, count, revenue, date) VALUES (?, ?, ?, ?, ?)"
            self.cursor.execute(cmd, (int(line['shelf_id']), str(line['name']), int(line['count']), int(line['revenue']), str(line['date'])))
        
        self.connection.commit()
    
    def SendQuery(self, query):
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        return rows