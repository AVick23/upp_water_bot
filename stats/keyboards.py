"""
Keyboard layouts for statistics module
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import date, timedelta

from config import Locale
from stats.constants import PERIODS


def get_stats_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Main statistics keyboard"""
    keyboard = []
    row = []
    
    for i, (period_id, period) in enumerate(PERIODS.items()):
        if period_id == "all":
            continue  # Skip all time for main keyboard
            
        btn_text = period[f"name_{lang}"]
        row.append(InlineKeyboardButton(btn_text, callback_data=f"stats_{period_id}"))
        
        if len(row) == 2 or i == len(PERIODS) - 2:  # 2 buttons per row
            keyboard.append(row)
            row = []
    
    # All time button
    keyboard.append([
        InlineKeyboardButton(PERIODS["all"][f"name_{lang}"], callback_data="stats_all")
    ])
    
    # Back button
    keyboard.append([
        InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_detailed_stats_keyboard(
    period: str,
    current_date: date,
    lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Keyboard for detailed period statistics with navigation"""
    keyboard = []
    
    # Navigation for week/month views
    if period in ["week", "month"]:
        nav_row = []
        
        # Previous period
        prev_date = current_date - timedelta(days=PERIODS[period]["days"])
        nav_row.append(
            InlineKeyboardButton("◀️", callback_data=f"stats_{period}_{prev_date.isoformat()}")
        )
        
        # Current period indicator
        nav_row.append(
            InlineKeyboardButton(
                current_date.strftime("%b %Y" if period == "month" else "%d.%m"),
                callback_data="stats_current"
            )
        )
        
        # Next period (if not in future)
        next_date = current_date + timedelta(days=PERIODS[period]["days"])
        if next_date <= date.today():
            nav_row.append(
                InlineKeyboardButton("▶️", callback_data=f"stats_{period}_{next_date.isoformat()}")
            )
        else:
            nav_row.append(InlineKeyboardButton("⏹️", callback_data="stats_noop"))
        
        keyboard.append(nav_row)
    
    # Export options
    keyboard.extend([
        [
            InlineKeyboardButton("📊 CSV", callback_data=f"export_csv_{period}"),
            InlineKeyboardButton("📋 JSON", callback_data=f"export_json_{period}"),
        ],
        [
            InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="stats")
        ]
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_comparison_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for comparing periods"""
    keyboard = [
        [
            InlineKeyboardButton("📊 vs Прошлая неделя", callback_data="compare_week_prev"),
            InlineKeyboardButton("📊 vs Прошлый месяц", callback_data="compare_month_prev"),
        ],
        [
            InlineKeyboardButton("📈 Тренды", callback_data="stats_trends"),
            InlineKeyboardButton("🔥 Серии", callback_data="stats_streaks"),
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="stats")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_heatmap_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for heatmap visualization options"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Месяц", callback_data="heatmap_month"),
            InlineKeyboardButton("📆 3 месяца", callback_data="heatmap_3month"),
        ],
        [
            InlineKeyboardButton("📊 По дням недели", callback_data="heatmap_weekdays"),
            InlineKeyboardButton("⏰ По времени", callback_data="heatmap_time"),
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="stats")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_export_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Keyboard for export options"""
    keyboard = [
        [
            InlineKeyboardButton("📊 CSV (Все данные)", callback_data="export_csv_all"),
            InlineKeyboardButton("📋 JSON (Все данные)", callback_data="export_json_all"),
        ],
        [
            InlineKeyboardButton("📅 Только этот месяц", callback_data="export_csv_month"),
            InlineKeyboardButton("📆 Только эту неделю", callback_data="export_csv_week"),
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="stats")],
    ]
    return InlineKeyboardMarkup(keyboard)