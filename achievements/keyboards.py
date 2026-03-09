"""
Keyboard layouts for achievements module
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional

from config import Locale, AchievementType
from achievements.constants import ACHIEVEMENT_CATEGORIES, RARITY_DISPLAY


def get_achievements_main_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Main achievements menu keyboard"""
    keyboard = []
    
    # Categories in rows of 2
    row = []
    for i, (cat_id, category) in enumerate(ACHIEVEMENT_CATEGORIES.items()):
        btn_text = f"{category['icon']} {category[f'name_{lang}']}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"ach_cat_{cat_id}"))
        
        if len(row) == 2 or i == len(ACHIEVEMENT_CATEGORIES) - 1:
            keyboard.append(row)
            row = []
    
    # Statistics and back buttons
    keyboard.extend([
        [
            InlineKeyboardButton("📊 " + ("Статистика", "Statistics")[lang == "en"], 
                               callback_data="ach_stats"),
            InlineKeyboardButton("🔍 " + ("Поиск", "Search")[lang == "en"], 
                               callback_data="ach_search"),
        ],
        [
            InlineKeyboardButton("🏆 " + ("Редкие", "Rare")[lang == "en"], 
                               callback_data="ach_rarity_rare"),
            InlineKeyboardButton("✨ " + ("Последние", "Recent")[lang == "en"], 
                               callback_data="ach_recent"),
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="main_menu")],
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_category_keyboard(category_id: str, earned_ids: List[str], lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for specific achievement category"""
    keyboard = []
    row = []
    
    category = ACHIEVEMENT_CATEGORIES.get(category_id, {})
    achievements = category.get("types", [])
    
    for i, ach_type in enumerate(achievements):
        ach_id = ach_type.value
        is_earned = ach_id in earned_ids
        
        # Different emoji based on earned status
        emoji = "✅" if is_earned else "🔲"
        btn_text = f"{emoji} {get_achievement_short_name(ach_type, lang)}"
        
        row.append(InlineKeyboardButton(btn_text, callback_data=f"ach_detail_{ach_id}"))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Navigation
    keyboard.extend([
        [InlineKeyboardButton("🏆 " + ("Все категории", "All categories")[lang == "en"], 
                             callback_data="achievements")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="achievements")],
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_rarity_keyboard(rarity: str, earned_ids: List[str], lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for achievements by rarity"""
    from config import ACHIEVEMENTS
    
    keyboard = []
    row = []
    
    # Filter achievements by rarity
    rarity_achievements = []
    for ach_type, info in ACHIEVEMENTS.items():
        if info.get("rarity") == rarity:
            rarity_achievements.append(ach_type)
    
    for i, ach_type in enumerate(rarity_achievements):
        ach_id = ach_type.value
        is_earned = ach_id in earned_ids
        
        emoji = "✅" if is_earned else RARITY_DISPLAY[rarity]["emoji"]
        btn_text = f"{emoji} {get_achievement_short_name(ach_type, lang)}"
        
        row.append(InlineKeyboardButton(btn_text, callback_data=f"ach_detail_{ach_id}"))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="achievements")])
    
    return InlineKeyboardMarkup(keyboard)


def get_achievement_detail_keyboard(
    ach_type: AchievementType,
    is_earned: bool,
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for achievement detail view"""
    keyboard = []
    
    if is_earned:
        # Share button for earned achievements
        keyboard.append([
            InlineKeyboardButton("📢 " + ("Поделиться", "Share")[lang == "en"], 
                               callback_data=f"ach_share_{ach_type.value}")
        ])
    else:
        # Track progress button for unearned
        keyboard.append([
            InlineKeyboardButton("📊 " + ("Отслеживать", "Track")[lang == "en"], 
                               callback_data=f"ach_track_{ach_type.value}")
        ])
    
    # Similar achievements
    similar = get_similar_achievements(ach_type)
    if similar:
        similar_btn = "🔄 " + ("Похожие", "Similar")[lang == "en"]
        keyboard.append([InlineKeyboardButton(similar_btn, callback_data="ach_similar")])
    
    # Navigation
    keyboard.extend([
        [InlineKeyboardButton("◀️ " + ("Назад", "Back")[lang == "en"], 
                             callback_data="achievements")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="main_menu")],
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_achievement_share_keyboard(ach_type: AchievementType, lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for sharing achievements"""
    keyboard = [
        [
            InlineKeyboardButton("📱 Telegram", callback_data=f"ach_share_tg_{ach_type.value}"),
            InlineKeyboardButton("📋 " + ("Копировать", "Copy")[lang == "en"], 
                               callback_data=f"ach_share_copy_{ach_type.value}"),
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data=f"ach_detail_{ach_type.value}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_achievement_progress_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for achievement progress tracking"""
    keyboard = [
        [
            InlineKeyboardButton("📊 " + ("Общий прогресс", "Overall")[lang == "en"], 
                               callback_data="ach_progress_all"),
            InlineKeyboardButton("🎯 " + ("Ближайшие", "Next")[lang == "en"], 
                               callback_data="ach_progress_next"),
        ],
        [
            InlineKeyboardButton("⚡ " + ("Быстрые", "Quick")[lang == "en"], 
                               callback_data="ach_progress_quick"),
            InlineKeyboardButton("🔥 " + ("Сложные", "Hard")[lang == "en"], 
                               callback_data="ach_progress_hard"),
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="achievements")],
    ]
    return InlineKeyboardMarkup(keyboard)


# Helper functions
def get_achievement_short_name(ach_type: AchievementType, lang: str = "ru") -> str:
    """Get short name for achievement (for buttons)"""
    from config import ACHIEVEMENTS
    info = ACHIEVEMENTS.get(ach_type, {})
    emoji = info.get("emoji", "🏆")
    
    # Get localized name from config (assuming it exists)
    from config import Locale
    name_key = f"ach_{ach_type.value}"
    name = Locale.get(name_key, lang)
    
    # Truncate if too long
    if len(name) > 20:
        name = name[:18] + "…"
    
    return f"{emoji} {name}"


def get_similar_achievements(ach_type: AchievementType) -> List[AchievementType]:
    """Get similar achievements (same category)"""
    for category_id, category in ACHIEVEMENT_CATEGORIES.items():
        if ach_type in category["types"]:
            # Return first 3 other achievements in same category
            others = [t for t in category["types"] if t != ach_type]
            return others[:3]
    return []