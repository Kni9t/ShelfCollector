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
        dateFromFiles = self.getDate()
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
        
        self.writeDate(dateFromFiles)

    def GetUserAuthorizationState(self, idUser):
        dateFromFiles = self.getDate()

        for id in dateFromFiles:
            if (id == idUser):
                return dateFromFiles[id]['authorizationState']
            
        return None
            
    def GetUsersMarket(self, idUser):
        dateFromFiles = self.getDate()

        for id in dateFromFiles:
            if (id == idUser):
                return dateFromFiles[id]['selectedMarket']
        
        return None
    
    def GetSalesCollectState(self, idUser):
        dateFromFiles = self.getDate()

        for id in dateFromFiles:
            if (id == idUser):
                return dateFromFiles[id]['salesCollectState']
            
        return None
        
    def AddNewUser(self, date):
        if (os.path.isfile(self.fileName)):
            dateFromFiles = self.getDate()
            for key in date:
                dateFromFiles[str(key)] = date[str(key)]
                
            self.writeData()
        else:
            self.writeDate(date)