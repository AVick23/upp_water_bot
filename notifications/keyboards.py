"""
Keyboard layouts for notifications module
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional, List

from config import Locale
from notifications.constants import NOTIFICATION_PRESETS, TIME_PRESETS
from datetime import datetime


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
    
    keyboard: List[List[InlineKeyboardButton]] = [
        [InlineKeyboardButton(
            f"🔔 {'Статус:' if lang == 'ru' else 'Status:'} {status_text}",
            callback_data="toggle_notifications"
        )],
        [
            InlineKeyboardButton(
                f"⏰ {'Начало' if lang == 'ru' else 'Start'}: {start_str}",
                callback_data="set_notif_start"
            ),
            InlineKeyboardButton(
                f"⏰ {'Конец' if lang == 'ru' else 'End'}: {end_str}",
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
        
        name_key = f"name_{lang}"
        btn_text = f"{preset[name_key]} ({start_str}-{end_str})"
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
    
    # Hours row (0-23 in groups of 4)
    hours_row = []
    for hour in range(0, 24, 4):
        hour_end = min(hour + 3, 23)
        btn_text = f"{hour:02d}-{hour_end:02d}"
        hours_row.append(InlineKeyboardButton(
            btn_text,
            callback_data=f"time_hour_range_{time_type}_{hour}_{hour_end}"
        ))
    
    # Quick presets
    quick_picks = []
    for preset in TIME_PRESETS[:5]:  # First 5 presets
        quick_picks.append(InlineKeyboardButton(
            preset[lang],
            callback_data=f"time_set_{time_type}_{preset['minutes']}"
        ))
    
    # More quick picks in second row
    quick_picks2 = []
    for preset in TIME_PRESETS[5:]:  # Last 3 presets
        quick_picks2.append(InlineKeyboardButton(
            preset[lang],
            callback_data=f"time_set_{time_type}_{preset['minutes']}"
        ))
    
    # Current time button
    now = datetime.now()
    now_minutes = now.hour * 60 + now.minute
    now_text = f"🕐 {now.hour:02d}:{now.minute:02d}"
    
    keyboard = [
        hours_row,
        quick_picks,
        quick_picks2 if quick_picks2 else [],
        [InlineKeyboardButton(now_text, callback_data=f"time_now_{time_type}")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings_notifications")],
    ]
    
    # Remove empty rows
    keyboard = [row for row in keyboard if row]
    
    return InlineKeyboardMarkup(keyboard)


def get_minute_picker_keyboard(
    time_type: str,
    hour: int,
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for picking minutes (0,15,30,45)"""
    keyboard = []
    
    # Minutes in 2 rows of 2
    minutes_row1 = []
    minutes_row2 = []
    
    for i, minute in enumerate([0, 15, 30, 45]):
        time_str = f"{hour:02d}:{minute:02d}"
        btn = InlineKeyboardButton(
            time_str,
            callback_data=f"time_set_{time_type}_{hour*60 + minute}"
        )
        if i < 2:
            minutes_row1.append(btn)
        else:
            minutes_row2.append(btn)
    
    keyboard.append(minutes_row1)
    keyboard.append(minutes_row2)
    
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


def get_notification_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for notification messages with quick add"""
    keyboard = [
        [InlineKeyboardButton(
            Locale.get("main_add_water", lang),
            callback_data="add_water"
        )]
    ]
    return InlineKeyboardMarkup(keyboard)