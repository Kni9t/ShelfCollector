import os
import json
from datetime import datetime

from collector.json_controller import JsonController

'''
'1234536': {
        'authorizationState': False,
        'salesCollectState': False,
        'addNewMarket': False,
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
                'addNewMarket': False,
                'market_detail': False,
                'selectedMarket': None
            }
            dateFromFiles[idUser][stats] = value
        
        self.writeData(dateFromFiles)
        
    def ResetAllState(self, idUser):
        self.SetUserStats(idUser, 'authorizationState', False)
        self.SetUserStats(idUser, 'salesCollectState', False)
        self.SetUserStats(idUser, 'addNewMarket', False)
        self.SetUserStats(idUser, 'market_detail', False)
    
    def GetState(self, idUser, state):
        idUser = str(idUser)
        dateFromFiles = self.getData()
        
        for id in dateFromFiles:
            if (id == idUser):
                return dateFromFiles[id][state]
            
        return None
        
    def AddNewUser(self, date):
        if (os.path.isfile(self.fileName)):
            dateFromFiles = self.getData()
            for key in date:
                dateFromFiles[int(key)] = date[int(key)]
                
            self.writeData()
        else:
            self.writeData(date)