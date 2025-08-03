import os
import json
from datetime import datetime

from collector.json_controller import JsonController

'''
'1234536': {
        'authorizationState': False,
        'salesCollectState': False,
        'selectedMarket': 'market name' or None
    }
'''

class StateController(JsonController):
    def SetUserStats(self, idUser, stats, value):
        idUser = str(idUser)
        dateFromFiles = self.getData()
        change = False

        for id in dateFromFiles:
            if id == idUser:
                dateFromFiles[id][stats] = value
                change = True

        if (change == False):
            dateFromFiles[idUser] = {
                'authorizationState': False,
                'salesCollectState': False,
                'selectedMarket': None
            }
            dateFromFiles[idUser][stats] = value
        
        self.writeData(dateFromFiles)

    def GetUserAuthorizationState(self, idUser):
        idUser = str(idUser)
        dateFromFiles = self.getData()

        for id in dateFromFiles:
            if (id == idUser):
                return dateFromFiles[id]['authorizationState']
            
        return None
            
    def GetUsersMarket(self, idUser):
        idUser = str(idUser)
        dateFromFiles = self.getData()

        for id in dateFromFiles:
            if (id == idUser):
                return dateFromFiles[id]['selectedMarket']
        
        return None
    
    def GetSalesCollectState(self, idUser):
        idUser = str(idUser)
        dateFromFiles = self.getData()
        
        for id in dateFromFiles:
            if (id == idUser):
                return dateFromFiles[id]['salesCollectState']
            
        return None
        
    def AddNewUser(self, date):
        if (os.path.isfile(self.fileName)):
            dateFromFiles = self.getData()
            for key in date:
                dateFromFiles[int(key)] = date[int(key)]
                
            self.writeData()
        else:
            self.writeData(date)