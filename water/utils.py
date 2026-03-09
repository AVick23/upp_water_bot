"""
Utility functions for water tracking
"""

import random
from typing import Dict, List, Tuple, Optional
from datetime import datetime, date

from config import DrinkType, DRINK_COEFFICIENTS
from db import (
    get_today_total, get_user, add_favorite_volume,
    get_favorite_volumes, get_user_stats
)
from water.constants import SUCCESS_MESSAGES, COEFFICIENT_INFO, VOLUME_RECOMMENDATIONS, DRINK_NAMES, WATER_PRESETS


def calculate_effective_volume(volume_ml: int, drink_type: DrinkType) -> int:
    """Calculate effective water volume based on drink type coefficient"""
    coefficient = DRINK_COEFFICIENTS.get(drink_type, 1.0)
    return int(volume_ml * coefficient)


def get_drink_coefficient_percent(drink_type: DrinkType) -> int:
    """Get coefficient as percentage for display"""
    coeff = DRINK_COEFFICIENTS.get(drink_type, 1.0)
    return int(coeff * 100)


def format_drink_info(drink_type: DrinkType, volume: int, lang: str = "ru") -> str:
    """Format drink information for display"""
    drink_name = DRINK_NAMES.get(drink_type, {}).get(lang, str(drink_type))
    effective = calculate_effective_volume(volume, drink_type)
    coeff_percent = get_drink_coefficient_percent(drink_type)
    
    if effective == volume:
        return f"{drink_name}: {volume} мл"
    else:
        return f"{drink_name}: {volume} мл → {effective} мл ({coeff_percent}%)"


def get_random_success_message(lang: str = "ru") -> str:
    """Get random success message"""
    messages = SUCCESS_MESSAGES.get(lang, SUCCESS_MESSAGES["ru"])
    return random.choice(messages)


def format_success_message(
    volume: int,
    effective: int,
    drink_type: DrinkType,
    lang: str = "ru"
) -> str:
    """Format success message after adding drink"""
    drink_name = DRINK_NAMES.get(drink_type, {}).get(lang, str(drink_type))
    
    if effective == volume:
        return f"✅ {volume} мл {drink_name}\n\n{get_random_success_message(lang)}"
    else:
        coeff_percent = get_drink_coefficient_percent(drink_type)
        return (
            f"✅ {volume} мл {drink_name}\n"
            f"📊 Засчитано: {effective} мл ({coeff_percent}%)\n\n"
            f"{get_random_success_message(lang)}"
        )


async def check_daily_goal_completion(user_id: int) -> Tuple[bool, int, int]:
    """Check if daily goal is completed and return progress"""
    user = await get_user(user_id)
    if not user:
        return False, 0, 0
    
    today_total = await get_today_total(user_id)
    from services import get_user_daily_norm
    goal = get_user_daily_norm(user_id)
    
    return today_total >= goal, today_total, goal


def get_volume_recommendation(volume: int, lang: str = "ru") -> str:
    """Get recommendation text based on volume"""
    if volume <= 200:
        return VOLUME_RECOMMENDATIONS["small"][lang]
    elif volume <= 300:
        return VOLUME_RECOMMENDATIONS["medium"][lang]
    elif volume <= 600:
        return VOLUME_RECOMMENDATIONS["large"][lang]
    else:
        return VOLUME_RECOMMENDATIONS["extra"][lang]


def suggest_next_volume(current_total: int, goal: int) -> int:
    """Suggest next volume based on remaining goal"""
    remaining = goal - current_total
    
    if remaining <= 0:
        return 0
    elif remaining <= 150:
        return remaining
    elif remaining <= 250:
        return 250
    elif remaining <= 500:
        return 500
    else:
        return 250  # Default suggestion


async def update_favorite_volume(user_id: int, volume: int) -> List[int]:
    """Add volume to user's favorites"""
    return await add_favorite_volume(user_id, volume)


async def get_available_volumes(user_id: int) -> Dict[str, List[int]]:
    """Get standard and favorite volumes"""
    favorites = await get_favorite_volumes(user_id)
    
    return {
        "standard": WATER_PRESETS,
        "favorites": favorites
    }


def get_time_based_greeting(lang: str = "ru") -> str:
    """Get greeting based on time of day"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "☀️ " + ("Доброе утро!" if lang == "ru" else "Good morning!")
    elif 12 <= hour < 18:
        return "🌤️ " + ("Добрый день!" if lang == "ru" else "Good afternoon!")
    elif 18 <= hour < 22:
        return "🌅 " + ("Добрый вечер!" if lang == "ru" else "Good evening!")
    else:
        return "🌙 " + ("Доброй ночи!" if lang == "ru" else "Good night!")


def validate_custom_volume(volume_str: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Validate custom volume input"""
    try:
        volume = int(volume_str)
        if 1 <= volume <= 5000:
            return True, volume, None
        elif volume <= 0:
            return False, None, "error_volume_too_small"
        else:
            return False, None, "error_volume_too_large"
    except ValueError:
        return False, None, "error_invalid_number"