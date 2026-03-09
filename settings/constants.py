"""
Constants for settings module
"""

from config import ActivityMode

# Timezone presets (most common timezones)
TIMEZONE_PRESETS = [
    {"name": "UTC-12:00", "tz": "Etc/GMT+12", "offset": -12},
    {"name": "UTC-11:00", "tz": "Etc/GMT+11", "offset": -11},
    {"name": "UTC-10:00", "tz": "Pacific/Honolulu", "offset": -10},
    {"name": "UTC-09:00", "tz": "America/Anchorage", "offset": -9},
    {"name": "UTC-08:00", "tz": "America/Los_Angeles", "offset": -8},
    {"name": "UTC-07:00", "tz": "America/Denver", "offset": -7},
    {"name": "UTC-06:00", "tz": "America/Chicago", "offset": -6},
    {"name": "UTC-05:00", "tz": "America/New_York", "offset": -5},
    {"name": "UTC-04:00", "tz": "America/Caracas", "offset": -4},
    {"name": "UTC-03:00", "tz": "America/Sao_Paulo", "offset": -3},
    {"name": "UTC-02:00", "tz": "Etc/GMT+2", "offset": -2},
    {"name": "UTC-01:00", "tz": "Atlantic/Azores", "offset": -1},
    {"name": "UTC+00:00", "tz": "UTC", "offset": 0},
    {"name": "UTC+01:00", "tz": "Europe/London", "offset": 1},
    {"name": "UTC+02:00", "tz": "Europe/Berlin", "offset": 2},
    {"name": "UTC+03:00", "tz": "Europe/Moscow", "offset": 3},
    {"name": "UTC+03:30", "tz": "Asia/Tehran", "offset": 3.5},
    {"name": "UTC+04:00", "tz": "Europe/Samara", "offset": 4},
    {"name": "UTC+04:30", "tz": "Asia/Kabul", "offset": 4.5},
    {"name": "UTC+05:00", "tz": "Asia/Yekaterinburg", "offset": 5},
    {"name": "UTC+05:30", "tz": "Asia/Kolkata", "offset": 5.5},
    {"name": "UTC+05:45", "tz": "Asia/Kathmandu", "offset": 5.75},
    {"name": "UTC+06:00", "tz": "Asia/Almaty", "offset": 6},
    {"name": "UTC+06:30", "tz": "Asia/Yangon", "offset": 6.5},
    {"name": "UTC+07:00", "tz": "Asia/Bangkok", "offset": 7},
    {"name": "UTC+08:00", "tz": "Asia/Singapore", "offset": 8},
    {"name": "UTC+08:30", "tz": "Asia/Pyongyang", "offset": 8.5},
    {"name": "UTC+09:00", "tz": "Asia/Tokyo", "offset": 9},
    {"name": "UTC+09:30", "tz": "Australia/Darwin", "offset": 9.5},
    {"name": "UTC+10:00", "tz": "Australia/Sydney", "offset": 10},
    {"name": "UTC+11:00", "tz": "Pacific/Noumea", "offset": 11},
    {"name": "UTC+12:00", "tz": "Pacific/Auckland", "offset": 12},
    {"name": "UTC+13:00", "tz": "Pacific/Tongatapu", "offset": 13},
    {"name": "UTC+14:00", "tz": "Pacific/Kiritimati", "offset": 14},
]

# Activity mode descriptions
MODE_DESCRIPTIONS = {
    ActivityMode.NORMAL: {
        "ru": "🏃 Обычный режим активности. Норма воды рассчитывается стандартно.",
        "en": "🏃 Normal activity mode. Water norm calculated normally."
    },
    ActivityMode.WORKOUT: {
        "ru": "💪 Режим тренировки. Норма увеличена на 30% для компенсации потерь.",
        "en": "💪 Workout mode. Norm increased by 30% to compensate for losses."
    },
    ActivityMode.FOCUS: {
        "ru": "🎯 Режим фокуса. Стандартная норма, рекомендуется пить регулярно.",
        "en": "🎯 Focus mode. Standard norm, recommended to drink regularly."
    },
    ActivityMode.VACATION: {
        "ru": "🏖️ Режим отпуска. Норма снижена на 20% для расслабленного режима.",
        "en": "🏖️ Vacation mode. Norm reduced by 20% for relaxed mode."
    }
}

# Mode multipliers
MODE_MULTIPLIERS = {
    ActivityMode.NORMAL: 1.0,
    ActivityMode.WORKOUT: 1.3,
    ActivityMode.FOCUS: 1.0,
    ActivityMode.VACATION: 0.8,
}

# Notification time presets (in minutes from midnight)
NOTIFICATION_PRESETS = {
    "early_bird": {"start": 6*60, "end": 22*60, "name_ru": "🦉 Ранняя пташка", "name_en": "🦉 Early bird"},
    "standard": {"start": 8*60, "end": 22*60, "name_ru": "😊 Стандартный", "name_en": "😊 Standard"},
    "night_owl": {"start": 10*60, "end": 2*60, "name_ru": "🌙 Сова", "name_en": "🌙 Night owl"},
    "workaholic": {"start": 7*60, "end": 23*60, "name_ru": "💼 Рабочий", "name_en": "💼 Work"},
    "athlete": {"start": 5*60, "end": 23*60, "name_ru": "💪 Спортивный", "name_en": "💪 Athletic"},
}

# Language options
LANGUAGES = [
    {"code": "ru", "name": "Русский", "flag": "🇷🇺", "native": "Русский"},
    {"code": "en", "name": "English", "flag": "🇬🇧", "native": "English"},
]

# Export format descriptions
EXPORT_FORMATS = {
    "csv": {
        "ru": "📊 CSV - для Excel и таблиц",
        "en": "📊 CSV - for Excel and spreadsheets"
    },
    "json": {
        "ru": "📋 JSON - для разработчиков",
        "en": "📋 JSON - for developers"
    }
}

# Settings categories
SETTINGS_CATEGORIES = {
    "profile": {
        "icon": "👤",
        "name_ru": "Профиль",
        "name_en": "Profile",
        "order": 1
    },
    "notifications": {
        "icon": "🔔",
        "name_ru": "Уведомления",
        "name_en": "Notifications",
        "order": 2
    },
    "timezone": {
        "icon": "🌍",
        "name_ru": "Часовой пояс",
        "name_en": "Timezone",
        "order": 3
    },
    "mode": {
        "icon": "🎭",
        "name_ru": "Режим активности",
        "name_en": "Activity mode",
        "order": 4
    },
    "language": {
        "icon": "🌐",
        "name_ru": "Язык",
        "name_en": "Language",
        "order": 5
    },
    "export": {
        "icon": "📤",
        "name_ru": "Экспорт данных",
        "name_en": "Export data",
        "order": 6
    },
    "danger": {
        "icon": "⚠️",
        "name_ru": "Опасная зона",
        "name_en": "Danger zone",
        "order": 7
    }
}

# Danger zone actions
DANGER_ACTIONS = {
    "reset_stats": {
        "icon": "🔄",
        "name_ru": "Сбросить статистику",
        "name_en": "Reset statistics",
        "confirm_ru": "Вы уверены? Это удалит всю историю воды!",
        "confirm_en": "Are you sure? This will delete all water history!"
    },
    "delete_account": {
        "icon": "🗑️",
        "name_ru": "Удалить аккаунт",
        "name_en": "Delete account",
        "confirm_ru": "Вы уверены? Это действие необратимо!",
        "confirm_en": "Are you sure? This action cannot be undone!"
    }
}