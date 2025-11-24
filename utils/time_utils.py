# utils/time_utils.py
from datetime import datetime
from zoneinfo import ZoneInfo 
import pytz

def get_user_local_time(user_timezone: str) -> datetime:
    """Возвращает текущее время в часовом поясе пользователя."""
    tz = pytz.timezone(user_timezone)
    return datetime.now(tz)

def get_user_local_date_str(user_timezone: str) -> str:
    """Возвращает текущую дату (YYYY-MM-DD) в часовом поясе пользователя."""
    return get_user_local_time(user_timezone).strftime("%Y-%m-%d")

def is_time_in_range(current_time: str, start: str, end: str) -> bool:
    """Проверяет, попадает ли current_time в [start, end]."""
    current = datetime.strptime(current_time, "%H:%M")
    start_dt = datetime.strptime(start, "%H:%M")
    end_dt = datetime.strptime(end, "%H:%M")
    return start_dt <= current <= end_dt

def get_user_local_time(timezone_str: str) -> datetime:
    tz = ZoneInfo(timezone_str)
    return datetime.now(tz)

def is_time_in_interval(current: str, start: str, end: str) -> bool:
    # Для упрощения: проверка только на точное совпадение с началом
    return current == start