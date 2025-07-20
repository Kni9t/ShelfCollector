from datetime import datetime, timedelta

class TimeController:
    def __init__(self):
        pass
        
    def CalculationWaitTime(self):
        now = datetime.now()
        next_day = now + timedelta(days = 1)
        next_time = next_day.replace(hour = 18, minute = 0, second = 0, microsecond = 0)

        sleep_seconds = int((next_time - now).total_seconds()) + 5
        
        return sleep_seconds, next_time