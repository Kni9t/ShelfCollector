import os
import json
from datetime import datetime

class JsonController:
    def __init__(self, bufFileName):
        self.fileName = bufFileName
        if (os.path.isfile(self.fileName)):
            pass
        else:
            file = open(self.fileName, 'w', encoding='utf8')
            file.close()

    def getData(self):
        if (os.path.isfile(self.fileName)):
            try:
                file = open(self.fileName, 'r', encoding='utf8')
                strList = json.load(file)
                file.close()
                return strList
            except:
                return {}
        else:
            return {}
    
    def writeData(self, date):
        with open(self.fileName, "w", encoding='utf8') as outfile:
                outfile.write(json.dumps(date))
                outfile.close()