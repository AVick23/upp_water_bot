"""
Utility functions for notifications module
"""

import re
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from notifications.constants import NOTIFICATION_PRESETS, TIME_CATEGORIES


def format_notification_time(minutes: int) -> str:
    """Format minutes from midnight to HH:MM string"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def parse_notification_time(time_str: str) -> Optional[int]:
    """
    Parse time string (HH:MM) to minutes from midnight
    Returns None if invalid
    """
    match = re.match(r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$', time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        return hour * 60 + minute
    return None


def validate_notification_time(time_str: str) -> Tuple[bool, Optional[int]]:
    """
    Validate notification time string
    Returns (is_valid, minutes)
    """
    minutes = parse_notification_time(time_str)
    if minutes is not None:
        return True, minutes
    return False, None


def get_notification_preset(preset_id: str) -> Optional[Dict]:
    """Get notification preset by ID"""
    return NOTIFICATION_PRESETS.get(preset_id)


def get_time_category(hour: int) -> str:
    """Get time category for given hour"""
    for category, info in TIME_CATEGORIES.items():
        start, end = info["range"]
        if start <= hour < end:
            return category
    return "night"  # default


def get_time_recommendation(hour: int, lang: str = "ru") -> str:
    """Get recommendation based on time of day"""
    category = get_time_category(hour)
    
    recommendations = {
        "early_morning": {
            "ru": "🌌 Самое время для глубокого сна. Вода подождет до утра.",
            "en": "🌌 Time for deep sleep. Water can wait until morning."
        },
        "morning": {
            "ru": "🌅 Доброе утро! Начните день со стакана воды.",
            "en": "🌅 Good morning! Start your day with a glass of water."
        },
        "afternoon": {
            "ru": "☀️ Поддерживайте водный баланс в течение дня.",
            "en": "☀️ Maintain hydration throughout the day."
        },
        "evening": {
            "ru": "🌆 Вечером пейте воду умеренно, чтобы не нарушить сон.",
            "en": "🌆 Drink water moderately in the evening for better sleep."
        },
        "night": {
            "ru": "🌙 Ночью лучше не пить воду, чтобы не просыпаться.",
            "en": "🌙 Better not to drink at night to avoid waking up."
        }
    }
    
    return recommendations.get(category, recommendations["night"])[lang]


def calculate_next_notification_time(
    current_time: datetime,
    interval_minutes: int,
    start_minutes: int,
    end_minutes: int,
    timezone: str = "UTC"
) -> Optional[datetime]:
    """
    Calculate next notification time within window
    """
    try:
        tz = ZoneInfo(timezone)
        local_time = current_time.astimezone(tz)
        local_minutes = local_time.hour * 60 + local_time.minute
        
        # If current time is after end, next notification is tomorrow at start
        if local_minutes >= end_minutes:
            next_date = local_time.date() + timedelta(days=1)
            next_local = datetime.combine(
                next_date, 
                datetime.min.time(), 
                tzinfo=tz
            ) + timedelta(minutes=start_minutes)
            return next_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        
        # Calculate next time within today
        next_minutes = local_minutes + interval_minutes
        if next_minutes > end_minutes:
            next_minutes = start_minutes + (next_minutes - end_minutes)
            next_date = local_time.date() + timedelta(days=1)
        else:
            next_date = local_time.date()
        
        next_local = datetime.combine(
            next_date,
            datetime.min.time(),
            tzinfo=tz
        ) + timedelta(minutes=next_minutes)
        
        return next_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        
    except Exception as e:
        return None


def get_interval_for_time_of_day(hour: int) -> int:
    """Get appropriate notification interval based on time of day"""
    from notifications.constants import TIME_BASED_INTERVALS
    
    if 6 <= hour < 12:
        return TIME_BASED_INTERVALS["morning"]
    elif 12 <= hour < 18:
        return TIME_BASED_INTERVALS["afternoon"]
    elif 18 <= hour < 22:
        return TIME_BASED_INTERVALS["evening"]
    else:
        return TIME_BASED_INTERVALS["night"]


def format_notification_summary(
    enabled: bool,
    start_minutes: int,
    end_minutes: int,
    lang: str = "ru"
) -> str:
    """Format notification settings summary"""
    status = "✅ Включены" if enabled else "❌ Выключены" if lang == "ru" else "✅ Enabled" if enabled else "❌ Disabled"
    time_range = f"{format_notification_time(start_minutes)} - {format_notification_time(end_minutes)}"
    
    if lang == "ru":
        return f"🔔 **Уведомления:** {status}\n⏰ **Время:** {time_range}"
    else:
        return f"🔔 **Notifications:** {status}\n⏰ **Time:** {time_range}"