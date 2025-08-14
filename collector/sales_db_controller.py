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
            
        cmd = f"CREATE TABLE IF NOT EXISTS markets (market_id INTEGER PRIMARY KEY AUTOINCREMENT, hash TEXT, name TEXT, start_date TEXT, end_date TEXT, location TEXT)"
        self.cursor.execute(cmd)
        
        cmd = f"CREATE TABLE IF NOT EXISTS market_sales (id INTEGER PRIMARY KEY AUTOINCREMENT, market_id INTEGER, date TEXT, time TEXT, revenue INTEGER, cash TEXT, sender_id TEXT, sender_name TEXT, FOREIGN KEY(market_id) REFERENCES markets(id))"
        self.cursor.execute(cmd)
        
        cmd = f"CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, shelf_id INTEGER, name TEXT, count INTEGER, revenue INTEGER, date TEXT, FOREIGN KEY(shelf_id) REFERENCES shelves(id))"
        self.cursor.execute(cmd)
        
    def AddShelfSale(self, dataDict):
        for line in dataDict:
            cmd = f"INSERT INTO sales (shelf_id, name, count, revenue, date) VALUES (?, ?, ?, ?, ?)"
            self.cursor.execute(cmd, (int(line['shelf_id']), str(line['name']), int(line['count']), int(line['revenue']), str(line['date'])))
        
        self.connection.commit()
        
    def AddMarkets(self, dataDict):
        cmd = f"INSERT INTO markets (hash, name, start_date, end_date, location) VALUES (?, ?, ?, ?, ?)"
        
        if (type(dataDict) is list):
            for line in dataDict:
                self.cursor.execute(cmd, (str(line['hash']), str(line['name']), str(line['start_date']), str(line['end_date']), str(line['location'])))
                
        elif (type(dataDict) is dict):
            self.cursor.execute(cmd, (str(dataDict['hash']), str(dataDict['name']), str(dataDict['start_date']), str(dataDict['end_date']), str(dataDict['location'])))
        
        self.connection.commit()
        
    def AddMarketsSale(self, dataDict: dict):
        cmd = f"INSERT INTO market_sales (market_id, date, time, revenue, cash, sender_id, sender_name) VALUES (?, ?, ?, ?, ?, ?, ?)"
        self.cursor.execute(cmd, (int(dataDict['market_id']), str(dataDict['date']), str(dataDict['time']), int(dataDict['revenue']), str(dataDict['cash']), str(dataDict['sender_id']), str(dataDict['sender_name'])))
        
        self.connection.commit()
        return self.cursor.lastrowid
    
    def GetAllMarketSales(self):
        cmd = "SELECT m.market_id, m.name AS market_name, m.start_date, SUM(CASE WHEN s.cash IN (1, '1', 't', 'true', 'True')  THEN s.revenue ELSE 0 END) AS revenue_cash, SUM(CASE WHEN s.cash IN (0, '0', 'f', 'false', 'False') THEN s.revenue ELSE 0 END) AS revenue_noncash, SUM(COALESCE(s.revenue,0)) AS revenue_total FROM markets AS m LEFT JOIN market_sales AS s ON s.market_id = m.market_id GROUP BY m.market_id, m.name ORDER BY m.market_id;"
        self.cursor.execute(cmd)
        rows = self.cursor.fetchall()
        salesList = []
        
        for row in rows:
            result = {
                'id': int(row[0]),
                'name': str(row[1]).capitalize(),
                'date': str(row[2]),
                'cash': int(row[3]),
                'online': int(row[4]),
                'total': int(row[5])
            }
            
            salesList.append(result)
            
        return salesList
    
    def GetMarketSaleById(self, sale_id: int):
        if (sale_id >= 0):
            self.cursor.execute(f"SELECT * FROM market_sales WHERE id = {sale_id}")
            row = self.cursor.fetchall()[0]
            
            sales = {
                "id": int(row[0]),
                "market_id": int(row[1]),
                "date": str(row[2]),
                "time": str(row[3]),
                "revenue": int(row[4]),
                "cash": str(row[5]),
                "sender_id": int(row[6]),
                "sender_name": str(row[7]),
            }
            
            return sales
        return None
    
    def GetAllMarkets(self):
        self.cursor.execute(f"SELECT * FROM markets")
        rows = self.cursor.fetchall()
        
        markets = []
        
        for row in rows:
            markets.append({
                "market_id": int(row[0]),
                "hash": str(row[1]),
                "name": str(row[2]).capitalize(),
                "start_date": str(row[3]),
                "end_date": str(row[4]),
                "location": str(row[5])
            })
            
        return markets
        
    
    def CheckSalesOwner(self, sale_id: int, user_id: int):
        sales = self.GetMarketSaleById(sale_id)
        if (sales):
            if (sales['sender_id'] == user_id):
                return True
            else:
                return False
        return None
    
    def RemoveMarketSaleById(self, sale_id: int):
        if (sale_id >= 0):
            sales = self.GetMarketSaleById(sale_id)
            self.cursor.execute(f"DELETE FROM market_sales WHERE id = {sale_id}")
            self.connection.commit()
            return sales
        return None
    
    def CheckMarketsHash(self, hash):
        marketsList = self.GetAllMarkets()
        
        for market in marketsList:
            if (hash == market["hash"]):
                return market
        
        return None
    
    def SendQuery(self, query):
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        return rows