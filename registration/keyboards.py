"""
Keyboard layouts for registration process
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import Locale, Gender, ActivityLevel
from registration.states import STATE_CITY


def get_start_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for welcome message"""
    keyboard = [
        [InlineKeyboardButton(Locale.get("btn_start", lang), callback_data="start_registration")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_gender_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for gender selection"""
    keyboard = [
        [
            InlineKeyboardButton(Locale.get("btn_male", lang), callback_data=f"gender_{Gender.MALE.value}"),
            InlineKeyboardButton(Locale.get("btn_female", lang), callback_data=f"gender_{Gender.FEMALE.value}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_activity_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for activity level selection"""
    keyboard = [
        [InlineKeyboardButton(Locale.get("activity_low", lang), callback_data=f"activity_{ActivityLevel.LOW.value}")],
        [InlineKeyboardButton(Locale.get("activity_medium", lang), callback_data=f"activity_{ActivityLevel.MEDIUM.value}")],
        [InlineKeyboardButton(Locale.get("activity_high", lang), callback_data=f"activity_{ActivityLevel.HIGH.value}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_city_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for city input with skip option"""
    keyboard = [
        [InlineKeyboardButton(Locale.get("reg_skip", lang), callback_data="skip_city")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard with cancel button"""
    keyboard = [
        [InlineKeyboardButton(Locale.get("btn_cancel", lang), callback_data="cancel_registration")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(lang: str = "ru", callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Generic back button keyboard"""
    keyboard = [
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data=callback_data)]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_profile_edit_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for profile editing"""
    keyboard = [
        [
            InlineKeyboardButton(Locale.get("profile_weight", lang), callback_data="edit_weight"),
            InlineKeyboardButton(Locale.get("profile_height", lang), callback_data="edit_height"),
        ],
        [
            InlineKeyboardButton(Locale.get("profile_gender", lang), callback_data="edit_gender"),
            InlineKeyboardButton(Locale.get("profile_activity", lang), callback_data="edit_activity"),
        ],
        [InlineKeyboardButton(Locale.get("profile_city", lang), callback_data="edit_city")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)