"""
Keyboard layouts for settings module
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional, Dict

from config import Locale, ActivityMode
from settings.constants import (
    SETTINGS_CATEGORIES, TIMEZONE_PRESETS, LANGUAGES,
    NOTIFICATION_PRESETS, DANGER_ACTIONS, MODE_DESCRIPTIONS
)


def get_settings_main_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Main settings menu keyboard"""
    keyboard = []
    
    # Sort categories by order
    sorted_categories = sorted(SETTINGS_CATEGORIES.items(), key=lambda x: x[1]["order"])
    
    for cat_id, category in sorted_categories:
        if cat_id == "danger":
            continue  # Danger zone at the bottom
        btn_text = f"{category['icon']} {category[f'name_{lang}']}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"settings_{cat_id}")])
    
    # Danger zone
    danger = SETTINGS_CATEGORIES["danger"]
    keyboard.append([InlineKeyboardButton(
        f"{danger['icon']} {danger[f'name_{lang}']}", 
        callback_data="settings_danger"
    )])
    
    # Back button
    keyboard.append([InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)


def get_profile_settings_keyboard(
    current_values: Dict[str, any],
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for profile settings"""
    keyboard = [
        [
            InlineKeyboardButton(
                f"⚖️ {Locale.get('profile_weight', lang)}: {current_values.get('weight', '?')} кг",
                callback_data="edit_weight"
            ),
            InlineKeyboardButton(
                f"📏 {Locale.get('profile_height', lang)}: {current_values.get('height', '?')} см",
                callback_data="edit_height"
            ),
        ],
        [
            InlineKeyboardButton(
                f"👤 {Locale.get('profile_gender', lang)}: {current_values.get('gender_display', '?')}",
                callback_data="edit_gender"
            ),
            InlineKeyboardButton(
                f"🏃 {Locale.get('profile_activity', lang)}: {current_values.get('activity_display', '?')}",
                callback_data="edit_activity"
            ),
        ],
        [
            InlineKeyboardButton(
                f"🏙️ {Locale.get('profile_city', lang)}: {current_values.get('city', '-')}",
                callback_data="edit_city"
            )
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_notifications_settings_keyboard(
    enabled: bool,
    start_minutes: int,
    end_minutes: int,
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for notification settings"""
    
    # Format time
    start_str = f"{start_minutes//60:02d}:{start_minutes%60:02d}"
    end_str = f"{end_minutes//60:02d}:{end_minutes%60:02d}"
    
    status_text = "✅ " + ("Включены", "Enabled")[lang == "en"] if enabled else "❌ " + ("Выключены", "Disabled")[lang == "en"]
    
    keyboard = [
        [InlineKeyboardButton(
            f"🔔 {Locale.get('notifications_status', lang)}: {status_text}",
            callback_data="toggle_notifications"
        )],
        [
            InlineKeyboardButton(
                f"⏰ {Locale.get('notif_start', lang)}: {start_str}",
                callback_data="set_notif_start"
            ),
            InlineKeyboardButton(
                f"⏰ {Locale.get('notif_end', lang)}: {end_str}",
                callback_data="set_notif_end"
            ),
        ],
        [InlineKeyboardButton(
            "🔄 " + ("Пресеты", "Presets")[lang == "en"],
            callback_data="notif_presets"
        )],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_notification_presets_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for notification presets"""
    keyboard = []
    
    for preset_id, preset in NOTIFICATION_PRESETS.items():
        start = preset["start"]
        end = preset["end"]
        start_str = f"{start//60:02d}:{start%60:02d}"
        end_str = f"{end//60:02d}:{end%60:02d}"
        
        btn_text = f"{preset[f'name_{lang}']} ({start_str}-{end_str})"
        keyboard.append([InlineKeyboardButton(
            btn_text,
            callback_data=f"notif_preset_{preset_id}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        Locale.get("btn_back", lang),
        callback_data="settings_notifications"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_time_picker_keyboard(
    time_type: str,  # "start" or "end"
    current_minutes: int,
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for picking time (hours and minutes)"""
    
    current_hour = current_minutes // 60
    current_min = current_minutes % 60
    
    # Hours row (0-23)
    hours_row = []
    for hour in range(0, 24, 4):
        hour_end = min(hour + 3, 23)
        btn_text = f"{hour:02d}-{hour_end:02d}"
        hours_row.append(InlineKeyboardButton(
            btn_text,
            callback_data=f"time_hour_range_{time_type}_{hour}_{hour_end}"
        ))
    
    # Quick picks
    quick_picks = [
        InlineKeyboardButton("🕐 Now", callback_data=f"time_now_{time_type}"),
        InlineKeyboardButton("🌅 06:00", callback_data=f"time_set_{time_type}_360"),
        InlineKeyboardButton("🌞 12:00", callback_data=f"time_set_{time_type}_720"),
        InlineKeyboardButton("🌆 18:00", callback_data=f"time_set_{time_type}_1080"),
        InlineKeyboardButton("🌙 22:00", callback_data=f"time_set_{time_type}_1320"),
    ]
    
    keyboard = [
        hours_row,
        quick_picks,
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings_notifications")],
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_minute_picker_keyboard(
    time_type: str,
    hour: int,
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for picking minutes (0,15,30,45)"""
    keyboard = []
    
    # Minutes in 4 columns
    minutes_row = []
    for minute in [0, 15, 30, 45]:
        time_str = f"{hour:02d}:{minute:02d}"
        minutes_row.append(InlineKeyboardButton(
            time_str,
            callback_data=f"time_set_{time_type}_{hour*60 + minute}"
        ))
    keyboard.append(minutes_row)
    
    # Custom minute input
    keyboard.append([InlineKeyboardButton(
        "✏️ " + ("Своё время", "Custom")[lang == "en"],
        callback_data=f"time_custom_{time_type}_{hour}"
    )])
    
    keyboard.append([InlineKeyboardButton(
        Locale.get("btn_back", lang),
        callback_data=f"set_notif_{time_type}"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_timezone_keyboard(
    current_tz: str = "UTC",
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for timezone selection"""
    keyboard = []
    row = []
    
    for i, tz_info in enumerate(TIMEZONE_PRESETS):
        # Mark current timezone
        marker = " ✓" if tz_info["tz"] == current_tz else ""
        btn_text = f"{tz_info['name']}{marker}"
        
        row.append(InlineKeyboardButton(
            btn_text,
            callback_data=f"tz_set_{tz_info['tz']}"
        ))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # Auto-detect button
    keyboard.append([InlineKeyboardButton(
        "📍 " + ("Определить автоматически", "Auto-detect")[lang == "en"],
        callback_data="tz_auto"
    )])
    
    keyboard.append([InlineKeyboardButton(
        Locale.get("btn_back", lang),
        callback_data="settings"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_mode_keyboard(
    current_mode: ActivityMode,
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for activity mode selection"""
    keyboard = []
    
    for mode in ActivityMode:
        # Check if current
        marker = " ✓" if mode == current_mode else ""
        
        # Get description
        desc = MODE_DESCRIPTIONS[mode][lang]
        short_desc = desc[:30] + "..." if len(desc) > 30 else desc
        
        btn_text = f"{mode_icon(mode)} {mode_name(mode, lang)}{marker}"
        keyboard.append([InlineKeyboardButton(
            btn_text,
            callback_data=f"mode_set_{mode.value}"
        )])
        keyboard.append([InlineKeyboardButton(
            f"ℹ️ {short_desc}",
            callback_data=f"mode_info_{mode.value}",
            url=None
        )])
    
    keyboard.append([InlineKeyboardButton(
        Locale.get("btn_back", lang),
        callback_data="settings"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_language_keyboard(
    current_lang: str = "ru",
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for language selection"""
    keyboard = []
    
    for language in LANGUAGES:
        marker = " ✓" if language["code"] == current_lang else ""
        btn_text = f"{language['flag']} {language['native']}{marker}"
        
        keyboard.append([InlineKeyboardButton(
            btn_text,
            callback_data=f"lang_set_{language['code']}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        Locale.get("btn_back", lang),
        callback_data="settings"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_export_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for export options"""
    keyboard = [
        [
            InlineKeyboardButton(
                "📊 CSV",
                callback_data="export_csv"
            ),
            InlineKeyboardButton(
                "📋 JSON",
                callback_data="export_json"
            ),
        ],
        [
            InlineKeyboardButton(
                "📅 " + ("Последний месяц", "Last month")[lang == "en"],
                callback_data="export_month"
            ),
            InlineKeyboardButton(
                "📆 " + ("Последняя неделя", "Last week")[lang == "en"],
                callback_data="export_week"
            ),
        ],
        [InlineKeyboardButton(
            Locale.get("btn_back", lang),
            callback_data="settings"
        )],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_danger_zone_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for danger zone actions"""
    keyboard = []
    
    for action_id, action in DANGER_ACTIONS.items():
        keyboard.append([InlineKeyboardButton(
            f"{action['icon']} {action[f'name_{lang}']}",
            callback_data=f"danger_{action_id}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        Locale.get("btn_back", lang),
        callback_data="settings"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(
    action: str,
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Confirmation keyboard for dangerous actions"""
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ " + ("Подтвердить", "Confirm")[lang == "en"],
                callback_data=f"confirm_{action}"
            ),
            InlineKeyboardButton(
                "❌ " + ("Отмена", "Cancel")[lang == "en"],
                callback_data=f"cancel_{action}"
            ),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# Helper functions
def mode_icon(mode: ActivityMode) -> str:
    """Get icon for activity mode"""
    icons = {
        ActivityMode.NORMAL: "🏃",
        ActivityMode.WORKOUT: "💪",
        ActivityMode.FOCUS: "🎯",
        ActivityMode.VACATION: "🏖️",
    }
    return icons.get(mode, "🎭")


def mode_name(mode: ActivityMode, lang: str = "ru") -> str:
    """Get localized mode name"""
    names = {
        ActivityMode.NORMAL: {"ru": "Обычный", "en": "Normal"},
        ActivityMode.WORKOUT: {"ru": "Тренировка", "en": "Workout"},
        ActivityMode.FOCUS: {"ru": "Фокус", "en": "Focus"},
        ActivityMode.VACATION: {"ru": "Отпуск", "en": "Vacation"},
    }
    return names.get(mode, {}).get(lang, str(mode))