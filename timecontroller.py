import logging
import time
from datetime import datetime, timedelta

class TimeController:
    def __init__(self):
        pass
        
    def CalculationWaitTime(self):
        now = datetime.now()
        next_hour = now + timedelta(days = 1)
        next_time = next_hour.replace(hour = 16, minute = 0, second = 0, microsecond = 0)

        print(datetime.now().day)
        print(next_time)

        sleep_seconds = int((next_time - now).total_seconds()) + 5
        
        return sleep_seconds