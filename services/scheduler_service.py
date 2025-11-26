# services/scheduler_service.py
from datetime import datetime, timedelta

def generate_reminder_schedule(start_time: str, end_time: str, glasses: int) -> list[str]:
    """
    Генерирует равномерное расписание уведомлений
    Первое - ровно в start_time, последнее - ровно в end_time
    """
    if glasses <= 1:
        return [start_time]  # Только одно уведомление
    
    start_dt = datetime.strptime(start_time, '%H:%M')
    end_dt = datetime.strptime(end_time, '%H:%M')
    
    total_minutes = (end_dt - start_dt).total_seconds() / 60
    interval = total_minutes / (glasses - 1)
    
    times = []
    for i in range(glasses):
        reminder_time = start_dt + timedelta(minutes=interval * i)
        times.append(reminder_time.strftime('%H:%M'))
    
    return times