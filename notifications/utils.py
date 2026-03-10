"""
Utility functions for notifications module
"""

import re
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from notifications.constants import NOTIFICATION_PRESETS, TIME_CATEGORIES

logger = logging.getLogger(__name__)


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
    # Поддерживаем форматы "ЧЧ:ММ" и "Ч:ММ"
    match = re.match(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$', time_str.strip())
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


def is_time_in_window(
    current_minutes: int,
    start_minutes: int,
    end_minutes: int
) -> bool:
    """
    Check if current time is within notification window.
    Correctly handles windows that cross midnight (end_minutes < start_minutes).
    """
    if end_minutes > start_minutes:
        # Normal window (e.g., 8:00 - 22:00)
        return start_minutes <= current_minutes < end_minutes
    else:
        # Window crosses midnight (e.g., 22:00 - 2:00)
        return current_minutes >= start_minutes or current_minutes < end_minutes


def calculate_next_notification_time(
    current_time: datetime,
    interval_minutes: int,
    start_minutes: int,
    end_minutes: int,
    timezone: str = "UTC"
) -> Optional[datetime]:
    """
    Calculate next notification time within window.
    Correctly handles windows that cross midnight.
    """
    try:
        tz = ZoneInfo(timezone)
        local_time = current_time.astimezone(tz)
        local_minutes = local_time.hour * 60 + local_time.minute
        
        # Check if we're in an active window
        in_window = is_time_in_window(local_minutes, start_minutes, end_minutes)
        
        if not in_window:
            # Not in window - find next window start
            if end_minutes > start_minutes:
                # Normal window, next start is today if before start, else tomorrow
                if local_minutes < start_minutes:
                    next_minutes = start_minutes
                    next_date = local_time.date()
                else:
                    next_minutes = start_minutes
                    next_date = local_time.date() + timedelta(days=1)
            else:
                # Window crosses midnight
                if local_minutes >= end_minutes and local_minutes < start_minutes:
                    # We're in the gap between end and start (e.g., 2:00-22:00)
                    next_minutes = start_minutes
                    next_date = local_time.date()
                else:
                    # We're after start but before midnight, or after midnight before end
                    # Actually we're in the window? This case should have been caught by in_window
                    next_minutes = start_minutes
                    next_date = local_time.date() + timedelta(days=1)
        else:
            # In window - calculate next interval
            next_minutes = local_minutes + interval_minutes
            
            # Check if next_minutes exceeds window end
            if end_minutes > start_minutes:
                # Normal window
                if next_minutes >= end_minutes:
                    next_minutes = start_minutes
                    next_date = local_time.date() + timedelta(days=1)
                else:
                    next_date = local_time.date()
            else:
                # Window crosses midnight
                if next_minutes >= 24 * 60:
                    # Wrapped to next day
                    next_minutes -= 24 * 60
                
                if next_minutes >= end_minutes and next_minutes < start_minutes:
                    # We've left the window (in the gap)
                    next_minutes = start_minutes
                    next_date = local_time.date() + timedelta(days=1)
                else:
                    next_date = local_time.date()
                    if next_minutes < local_minutes:
                        # We wrapped around midnight
                        next_date += timedelta(days=1)
        
        # Build next datetime
        next_local = datetime.combine(
            next_date,
            datetime.min.time(),
            tzinfo=tz
        ) + timedelta(minutes=next_minutes)
        
        # Don't schedule in the past
        if next_local <= local_time:
            next_local += timedelta(days=1)
        
        return next_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        
    except Exception as e:
        logger.error(f"Error calculating next notification time: {e}")
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


def clean_user_notification_data(context, user_id: int) -> None:
    """Clean up temporary notification data for a user"""
    keys_to_remove = [
        "notif_time_type",
        "hour_range",
        "selected_hour",
        "waiting_custom_time"
    ]
    for key in keys_to_remove:
        context.user_data.pop(key, None)