"""
Utility functions for settings module
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones

from config import Gender, ActivityLevel, ActivityMode
from db import get_user
from settings.constants import MODE_MULTIPLIERS, TIMEZONE_PRESETS, LANGUAGES


async def get_user_settings_display(user_id: int) -> Dict[str, Any]:
    """
    Get formatted user settings for display
    """
    user = await get_user(user_id)
    if not user:
        return {}
    
    # Format gender
    gender_display = "👨 Мужской" if user.gender == Gender.MALE else "👩 Женский" if user.gender == Gender.FEMALE else "?"
    
    # Format activity level
    activity_map = {
        ActivityLevel.LOW: "🐢 Низкая",
        ActivityLevel.MEDIUM: "🚶 Средняя",
        ActivityLevel.HIGH: "🏃 Высокая",
    }
    activity_display = activity_map.get(user.activity_level, "?")
    
    # Format notification times
    start_min = user.notification_start_minutes or 480
    end_min = user.notification_end_minutes or 1320
    notif_start = f"{start_min//60:02d}:{start_min%60:02d}"
    notif_end = f"{end_min//60:02d}:{end_min%60:02d}"
    
    # Format timezone
    tz_display = format_timezone_display(user.timezone or "UTC")
    
    # Format mode
    mode_display = format_mode_display(user.activity_mode or ActivityMode.NORMAL)
    
    return {
        "weight": user.weight,
        "height": user.height,
        "gender": user.gender,
        "gender_display": gender_display,
        "activity_level": user.activity_level,
        "activity_display": activity_display,
        "city": user.city or "-",
        "timezone": user.timezone or "UTC",
        "tz_display": tz_display,
        "notifications_enabled": user.notifications_enabled,
        "notification_start_minutes": user.notification_start_minutes or 480,
        "notification_end_minutes": user.notification_end_minutes or 1320,
        "notif_start": notif_start,
        "notif_end": notif_end,
        "activity_mode": user.activity_mode or ActivityMode.NORMAL,
        "mode_display": mode_display,
        "language": user.language or "ru",
    }


def format_timezone_display(tz_name: str) -> str:
    """Format timezone for display"""
    # Try to find in presets
    for preset in TIMEZONE_PRESETS:
        if preset["tz"] == tz_name:
            return preset["name"]
    
    # Try to get offset
    try:
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        offset = now.utcoffset()
        if offset:
            hours = offset.total_seconds() / 3600
            sign = "+" if hours >= 0 else ""
            return f"UTC{sign}{hours:.1f}".replace(".0", "")
    except:
        pass
    
    return tz_name


def format_mode_display(mode: ActivityMode, lang: str = "ru") -> str:
    """Format activity mode for display"""
    icons = {
        ActivityMode.NORMAL: "🏃",
        ActivityMode.WORKOUT: "💪",
        ActivityMode.FOCUS: "🎯",
        ActivityMode.VACATION: "🏖️",
    }
    
    names = {
        ActivityMode.NORMAL: {"ru": "Обычный", "en": "Normal"},
        ActivityMode.WORKOUT: {"ru": "Тренировка", "en": "Workout"},
        ActivityMode.FOCUS: {"ru": "Фокус", "en": "Focus"},
        ActivityMode.VACATION: {"ru": "Отпуск", "en": "Vacation"},
    }
    
    icon = icons.get(mode, "🎭")
    name = names.get(mode, {}).get(lang, str(mode))
    
    return f"{icon} {name}"


def get_mode_multiplier(mode: ActivityMode) -> float:
    """Get multiplier for activity mode"""
    return MODE_MULTIPLIERS.get(mode, 1.0)


def validate_time_format(time_str: str) -> Tuple[bool, Optional[int]]:
    """
    Validate time string (HH:MM) and return minutes from midnight
    """
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return False, None
        
        hour = int(parts[0])
        minute = int(parts[1])
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return True, hour * 60 + minute
    except:
        pass
    
    return False, None


def get_timezone_by_offset(offset_hours: float) -> Optional[str]:
    """
    Get timezone name by offset (approximate)
    """
    # Try exact match first
    for preset in TIMEZONE_PRESETS:
        if abs(preset["offset"] - offset_hours) < 0.01:
            return preset["tz"]
    
    # Try close match
    for preset in TIMEZONE_PRESETS:
        if abs(preset["offset"] - offset_hours) < 0.5:
            return preset["tz"]
    
    return None


async def auto_detect_timezone(lat: float, lon: float) -> Optional[str]:
    """
    Auto-detect timezone from coordinates
    Uses timezonefinder library if available
    """
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon)
        return tz_name
    except ImportError:
        # Fallback to offset-based detection
        return None
    except Exception:
        return None


def get_language_name(lang_code: str, display_lang: str = "ru") -> str:
    """Get localized language name"""
    for lang in LANGUAGES:
        if lang["code"] == lang_code:
            if display_lang == "ru":
                return f"{lang['flag']} {lang['name']}"
            else:
                return f"{lang['flag']} {lang['name']}"
    return lang_code


def get_notification_preset(preset_id: str) -> Optional[Dict]:
    """Get notification preset by ID"""
    from settings.constants import NOTIFICATION_PRESETS
    return NOTIFICATION_PRESETS.get(preset_id)


def format_settings_summary(settings: Dict[str, Any], lang: str = "ru") -> str:
    """Format settings summary for display"""
    lines = [
        "⚙️ **" + ("Настройки", "Settings")[lang == "en"] + "**\n",
        f"👤 **" + ("Профиль", "Profile")[lang == "en"] + "**:",
        f"  ⚖️ " + ("Вес", "Weight")[lang == "en"] + f": {settings['weight']} кг",
        f"  📏 " + ("Рост", "Height")[lang == "en"] + f": {settings['height']} см",
        f"  {settings['gender_display']}",
        f"  {settings['activity_display']}",
        f"  🏙️ " + ("Город", "City")[lang == "en"] + f": {settings['city']}\n",
        f"🔔 **" + ("Уведомления", "Notifications")[lang == "en"] + "**:",
        f"  " + ("Статус", "Status")[lang == "en"] + f": {'✅ ' + ('Вкл', 'On')[lang == 'en'] if settings['notifications_enabled'] else '❌ ' + ('Выкл', 'Off')[lang == 'en']}",
        f"  ⏰ {settings['notif_start']} - {settings['notif_end']}\n",
        f"🌍 **" + ("Часовой пояс", "Timezone")[lang == "en"] + f"**: {settings['tz_display']}\n",
        f"🎭 **" + ("Режим", "Mode")[lang == "en"] + f"**: {settings['mode_display']}\n",
        f"🌐 **" + ("Язык", "Language")[lang == "en"] + f"**: {get_language_name(settings['language'], lang)}",
    ]
    
    return "\n".join(lines)


def get_time_recommendation(hour: int) -> str:
    """Get recommendation based on time of day"""
    if 5 <= hour < 10:
        return "🌅 Утро - время начать пить воду!"
    elif 10 <= hour < 14:
        return "☀️ День - не забывай пить!"
    elif 14 <= hour < 18:
        return "🌤️ После обеда - еще немного воды"
    elif 18 <= hour < 22:
        return "🌆 Вечер - не забывай про воду"
    else:
        return "🌙 Ночь - отбой, вода подождет до утра"