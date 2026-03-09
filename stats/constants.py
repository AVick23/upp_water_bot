"""
Constants for statistics module
"""

from datetime import timedelta

# Period definitions
PERIODS = {
    "day": {
        "ru": "📅 День",
        "en": "📅 Day",
        "days": 1,
        "icon": "📅"
    },
    "week": {
        "ru": "📆 Неделя",
        "en": "📆 Week",
        "days": 7,
        "icon": "📆"
    },
    "month": {
        "ru": "🗓️ Месяц",
        "en": "🗓️ Month",
        "days": 30,
        "icon": "🗓️"
    },
    "year": {
        "ru": "📊 Год",
        "en": "📊 Year",
        "days": 365,
        "icon": "📊"
    },
    "all": {
        "ru": "💫 Всё время",
        "en": "💫 All time",
        "days": None,
        "icon": "💫"
    }
}

# Chart symbols for text-based visualization
CHART_SYMBOLS = {
    "bar_filled": "█",
    "bar_empty": "░",
    "bar_half": "▒",
    "bar_quarter": "▓",
    "trend_up": "📈",
    "trend_down": "📉",
    "trend_flat": "📊"
}

# Heatmap intensity levels (0-4)
HEATMAP_LEVELS = [
    {"min": 0, "max": 25, "symbol": "⚪", "name_ru": "Очень мало", "name_en": "Very low"},
    {"min": 26, "max": 50, "symbol": "🟢", "name_ru": "Мало", "name_en": "Low"},
    {"min": 51, "max": 75, "symbol": "🔵", "name_ru": "Средне", "name_en": "Medium"},
    {"min": 76, "max": 100, "symbol": "🟣", "name_ru": "Много", "name_en": "High"},
    {"min": 101, "max": 150, "symbol": "🔥", "name_ru": "Очень много", "name_en": "Very high"},
]

# Time of day statistics
TIME_SLOTS = [
    {"name_ru": "🌅 Утро (6-12)", "name_en": "🌅 Morning (6-12)", "start": 6, "end": 12},
    {"name_ru": "☀️ День (12-18)", "name_en": "☀️ Afternoon (12-18)", "start": 12, "end": 18},
    {"name_ru": "🌆 Вечер (18-24)", "name_en": "🌆 Evening (18-24)", "start": 18, "end": 24},
    {"name_ru": "🌙 Ночь (0-6)", "name_en": "🌙 Night (0-6)", "start": 0, "end": 6},
]

# Achievement stats messages
ACHIEVEMENT_STATS = {
    "ru": {
        "total": "🏆 Всего достижений: {count}",
        "by_rarity": "По редкости:",
        "common": "⚪ Обычных: {count}",
        "uncommon": "🟢 Необычных: {count}",
        "rare": "🔵 Редких: {count}",
        "epic": "🟣 Эпических: {count}",
        "legendary": "🟡 Легендарных: {count}",
        "mythic": "🔴 Мифических: {count}",
        "recent": "📅 Последние:",
    },
    "en": {
        "total": "🏆 Total achievements: {count}",
        "by_rarity": "By rarity:",
        "common": "⚪ Common: {count}",
        "uncommon": "🟢 Uncommon: {count}",
        "rare": "🔵 Rare: {count}",
        "epic": "🟣 Epic: {count}",
        "legendary": "🟡 Legendary: {count}",
        "mythic": "🔴 Mythic: {count}",
        "recent": "📅 Recent:",
    }
}

# Comparison messages
COMPARISON_MESSAGES = {
    "ru": {
        "better": "📈 Лучше предыдущего периода на {percent}%",
        "worse": "📉 Хуже предыдущего периода на {percent}%",
        "same": "📊 Так же, как в прошлом периоде",
        "record": "🏆 Это новый рекорд!",
        "average": "📊 Среднее: {value} мл/день",
    },
    "en": {
        "better": "📈 {percent}% better than previous period",
        "worse": "📉 {percent}% worse than previous period",
        "same": "📊 Same as previous period",
        "record": "🏆 This is a new record!",
        "average": "📊 Average: {value} ml/day",
    }
}

# Progress messages
PROGRESS_MESSAGES = {
    "ru": {
        "title": "📊 Прогресс за {period}",
        "total": "💧 Всего выпито: {value} мл",
        "days": "📅 Активных дней: {count}",
        "best_day": "🌟 Лучший день: {date} - {value} мл",
        "consistency": "🎯 Регулярность: {percent}%",
    },
    "en": {
        "title": "📊 Progress for {period}",
        "total": "💧 Total drunk: {value} ml",
        "days": "📅 Active days: {count}",
        "best_day": "🌟 Best day: {date} - {value} ml",
        "consistency": "🎯 Consistency: {percent}%",
    }
}