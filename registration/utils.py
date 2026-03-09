"""
Utility functions for registration process
"""

import re
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from telegram import Update
from zoneinfo import ZoneInfo

from db import get_user, update_user
from config import Locale, Gender, ActivityLevel
from services import calculate_water_norm


def validate_weight(weight_str: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate weight input
    Returns: (is_valid, weight_value, error_message)
    """
    try:
        weight = float(weight_str)
        if 30 <= weight <= 200:
            return True, weight, None
        else:
            return False, None, "error_range_weight"
    except ValueError:
        return False, None, "error_invalid_number"


def validate_height(height_str: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate height input
    Returns: (is_valid, height_value, error_message)
    """
    try:
        height = float(height_str)
        if 100 <= height <= 250:
            return True, height, None
        else:
            return False, None, "error_range_height"
    except ValueError:
        return False, None, "error_invalid_number"


def validate_city(city_str: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate city input (basic validation)
    Returns: (is_valid, city_value, error_message)
    """
    city = city_str.strip()
    if len(city) > 100:
        return False, None, "error_city_too_long"
    if re.search(r'[<>{}[\]\\]', city):  # Block potential injection
        return False, None, "error_invalid_chars"
    return True, city, None


def get_user_locale(update: Update) -> str:
    """Get user's language preference from Telegram"""
    if update.effective_user:
        lang_code = update.effective_user.language_code
        if lang_code and lang_code.lower().startswith("ru"):
            return "ru"
    return "en"


def calculate_user_norm(user_id: int) -> Dict[str, Any]:
    """Calculate and return user's water norm details"""
    user = get_user(user_id)
    if not user or not user.weight:
        return {}
    
    result = calculate_water_norm(
        weight=user.weight,
        gender=user.gender or Gender.MALE,
        activity_level=user.activity_level or ActivityLevel.MEDIUM
    )
    
    return {
        "base_norm": result.base_norm,
        "final_norm": result.final_norm,
        "weather_bonus": result.weather_bonus_percent,
        "mode_name": result.mode_name
    }


def format_registration_complete(user_id: int, lang: str = "ru") -> str:
    """Format registration completion message"""
    norm_data = calculate_user_norm(user_id)
    final_norm = norm_data.get("final_norm", 2000)
    
    return Locale.get("reg_complete_text", lang).format(norm=final_norm)


def get_localized_greeting(lang: str = "ru") -> str:
    """Get time-based greeting"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "☀️ " + ("Доброе утро!" if lang == "ru" else "Good morning!")
    elif 12 <= hour < 18:
        return "🌤️ " + ("Добрый день!" if lang == "ru" else "Good afternoon!")
    elif 18 <= hour < 22:
        return "🌅 " + ("Добрый вечер!" if lang == "ru" else "Good evening!")
    else:
        return "🌙 " + ("Доброй ночи!" if lang == "ru" else "Good night!")


def is_valid_timezone(tz_name: str) -> bool:
    """Check if timezone string is valid"""
    try:
        ZoneInfo(tz_name)
        return True
    except Exception:
        return False


def extract_user_data(update: Update) -> Dict[str, Any]:
    """Extract user data from Telegram update"""
    user = update.effective_user
    return {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language_code": user.language_code
    }


def create_registration_context() -> Dict[str, Any]:
    """Create empty registration context"""
    return {
        "weight": None,
        "height": None,
        "gender": None,
        "activity": None,
        "city": None,
        "timezone": "UTC"
    }