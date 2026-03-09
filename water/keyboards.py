"""
Keyboard layouts for water tracking
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional

from config import Locale, DrinkType
from water.constants import WATER_PRESETS, DRINK_CATEGORIES, DRINK_NAMES


def get_water_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for water volume selection"""
    keyboard = []
    
    # Volume presets in rows of 2
    row = []
    for i, preset in enumerate(WATER_PRESETS):
        btn_text = f"💧 {preset} мл" if lang == "ru" else f"💧 {preset} ml"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"water_{preset}"))
        
        if len(row) == 2 or i == len(WATER_PRESETS) - 1:
            keyboard.append(row)
            row = []
    
    # Custom volume and cancel
    keyboard.extend([
        [
            InlineKeyboardButton(Locale.get("add_custom", lang), callback_data="water_custom"),
            InlineKeyboardButton(Locale.get("btn_cancel", lang), callback_data="main_menu"),
        ]
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_drink_category_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for drink category selection"""
    keyboard = []
    
    for category_id, category in DRINK_CATEGORIES.items():
        name = category[f"name_{lang}"]
        keyboard.append([
            InlineKeyboardButton(name, callback_data=f"cat_{category_id}")
        ])
    
    keyboard.append([InlineKeyboardButton(Locale.get("btn_cancel", lang), callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)


def get_drink_type_keyboard(lang: str = "ru", category: str = "water") -> InlineKeyboardMarkup:
    """Keyboard for specific drink selection within category"""
    keyboard = []
    row = []
    
    category_drinks = DRINK_CATEGORIES.get(category, {}).get("drinks", [])
    
    for i, drink in enumerate(category_drinks):
        drink_name = DRINK_NAMES.get(drink, {}).get(lang, str(drink))
        callback = f"drink_{drink.value}"
        
        row.append(InlineKeyboardButton(drink_name, callback_data=callback))
        
        # 2 buttons per row
        if len(row) == 2 or i == len(category_drinks) - 1:
            keyboard.append(row)
            row = []
    
    # Back button
    keyboard.append([
        InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="drink_cat")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_quick_add_keyboard(
    lang: str = "ru",
    favorite_volumes: Optional[List[int]] = None
) -> InlineKeyboardMarkup:
    """Quick add keyboard with favorite volumes"""
    keyboard = []
    
    # Standard presets
    row = []
    for preset in WATER_PRESETS[:2]:
        btn_text = f"{preset} мл"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"quick_{preset}_water"))
    keyboard.append(row)
    
    row = []
    for preset in WATER_PRESETS[2:]:
        btn_text = f"{preset} мл"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"quick_{preset}_water"))
    keyboard.append(row)
    
    # Favorite volumes if any
    if favorite_volumes:
        row = []
        for vol in favorite_volumes[:3]:
            btn_text = f"⭐ {vol} мл"
            row.append(InlineKeyboardButton(btn_text, callback_data=f"quick_{vol}_water"))
        if row:
            keyboard.append(row)
    
    # Drink selection
    keyboard.append([
        InlineKeyboardButton(Locale.get("add_select_category", lang), callback_data="add_water")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_notification_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for notification messages with quick add"""
    keyboard = [
        [InlineKeyboardButton(Locale.get("main_add_water", lang), callback_data="add_water")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_favorite_management_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for managing favorite volumes"""
    keyboard = [
        [
            InlineKeyboardButton("➕ " + ("Добавить текущий", "Add current")[lang == "en"], 
                               callback_data="fav_add_current"),
            InlineKeyboardButton("🗑️ " + ("Очистить", "Clear")[lang == "en"], 
                               callback_data="fav_clear"),
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)