"""
Constants for notifications module
"""

from datetime import time
from typing import Dict, Any

# Notification time presets (in minutes from midnight)
NOTIFICATION_PRESETS = {
    "early_bird": {
        "start": 6 * 60,      # 6:00
        "end": 22 * 60,       # 22:00
        "name_ru": "🦉 Ранняя пташка",
        "name_en": "🦉 Early bird",
        "description_ru": "Активный день с раннего утра",
        "description_en": "Active day starting early morning"
    },
    "standard": {
        "start": 8 * 60,       # 8:00
        "end": 22 * 60,        # 22:00
        "name_ru": "😊 Стандартный",
        "name_en": "😊 Standard",
        "description_ru": "Оптимальный режим для большинства",
        "description_en": "Optimal mode for most people"
    },
    "night_owl": {
        "start": 10 * 60,      # 10:00
        "end": 2 * 60,         # 2:00 (следующего дня) - ВНИМАНИЕ: end < start!
        "name_ru": "🌙 Сова",
        "name_en": "🌙 Night owl",
        "description_ru": "Для тех, кто поздно ложится",
        "description_en": "For those who stay up late"
    },
    "workaholic": {
        "start": 7 * 60,       # 7:00
        "end": 23 * 60,        # 23:00
        "name_ru": "💼 Рабочий",
        "name_en": "💼 Work",
        "description_ru": "Полный рабочий день",
        "description_en": "Full work day schedule"
    },
    "athlete": {
        "start": 5 * 60,       # 5:00
        "end": 23 * 60,        # 23:00
        "name_ru": "💪 Спортивный",
        "name_en": "💪 Athletic",
        "description_ru": "Для активных тренировок",
        "description_en": "For active workouts"
    },
    "short": {
        "start": 9 * 60,       # 9:00
        "end": 18 * 60,        # 18:00
        "name_ru": "⏱️ Короткий",
        "name_en": "⏱️ Short",
        "description_ru": "Только в рабочее время",
        "description_en": "Only during work hours"
    }
}

# Notification types
NOTIFICATION_TYPES = {
    "smart_reminder": {
        "ru": "💧 Умное напоминание",
        "en": "💧 Smart reminder",
        "description_ru": "Адаптивное напоминание с расчетом интервалов",
        "description_en": "Adaptive reminder with interval calculation"
    },
    "morning": {
        "ru": "☀️ Утреннее",
        "en": "☀️ Morning",
        "description_ru": "Напоминание о начале дня",
        "description_en": "Start of day reminder"
    },
    "evening": {
        "ru": "🌙 Вечернее",
        "en": "🌙 Evening",
        "description_ru": "Итоги дня",
        "description_en": "Day summary"
    }
}

# Notification intervals (in minutes)
NOTIFICATION_INTERVALS = {
    "frequent": 30,      # каждые 30 минут
    "normal": 60,        # каждый час
    "relaxed": 120,      # каждые 2 часа
    "minimal": 180       # каждые 3 часа
}

# Time presets for quick selection
TIME_PRESETS = [
    {"minutes": 6 * 60, "ru": "🌅 06:00", "en": "🌅 06:00"},      # 6:00
    {"minutes": 8 * 60, "ru": "☀️ 08:00", "en": "☀️ 08:00"},      # 8:00
    {"minutes": 9 * 60, "ru": "💼 09:00", "en": "💼 09:00"},       # 9:00
    {"minutes": 12 * 60, "ru": "🍽️ 12:00", "en": "🍽️ 12:00"},     # 12:00
    {"minutes": 15 * 60, "ru": "☕ 15:00", "en": "☕ 15:00"},       # 15:00
    {"minutes": 18 * 60, "ru": "🌆 18:00", "en": "🌆 18:00"},      # 18:00
    {"minutes": 20 * 60, "ru": "📺 20:00", "en": "📺 20:00"},      # 20:00
    {"minutes": 22 * 60, "ru": "🌙 22:00", "en": "🌙 22:00"},      # 22:00
]

# Time of day categories
TIME_CATEGORIES = {
    "early_morning": {
        "range": (0, 6),
        "ru": "🌌 Глубокая ночь",
        "en": "🌌 Deep night",
        "emoji": "🌌"
    },
    "morning": {
        "range": (6, 12),
        "ru": "🌅 Утро",
        "en": "🌅 Morning",
        "emoji": "🌅"
    },
    "afternoon": {
        "range": (12, 18),
        "ru": "☀️ День",
        "en": "☀️ Afternoon",
        "emoji": "☀️"
    },
    "evening": {
        "range": (18, 22),
        "ru": "🌆 Вечер",
        "en": "🌆 Evening",
        "emoji": "🌆"
    },
    "night": {
        "range": (22, 24),
        "ru": "🌙 Ночь",
        "en": "🌙 Night",
        "emoji": "🌙"
    }
}

# Notification messages
NOTIFICATION_MESSAGES = {
    "smart": {
        "ru": [
            "💧 Время выпить стакан воды! Осталось {remaining} мл на сегодня.",
            "🌊 Напоминание о воде! Осталось выпить {remaining} мл.",
            "💪 Ещё {glasses} стаканов до цели! Продолжай в том же духе!",
            "🎯 Прогресс: {percent}% выполнено. Осталось {remaining} мл.",
            "✨ Маленький глоток здоровья! Осталось {remaining} мл.",
            "🌟 Твоя цель всё ближе! Осталось всего {glasses} стаканов.",
            "💧 Вода - источник жизни! Осталось {remaining} мл до нормы.",
            "🌅 Не забывай пить воду! Прогресс: {percent}%."
        ],
        "en": [
            "💧 Time for a glass of water! {remaining} ml left today.",
            "🌊 Hydration reminder! {remaining} ml left to drink.",
            "💪 {glasses} glasses to go! Keep up the good work!",
            "🎯 Progress: {percent}% complete. {remaining} ml remaining.",
            "✨ A sip of health! {remaining} ml left.",
            "🌟 Getting closer to your goal! Only {glasses} glasses left.",
            "💧 Water is life! {remaining} ml to reach your norm.",
            "🌅 Don't forget to drink water! Progress: {percent}%."
        ]
    },
    "morning": {
        "ru": [
            "☀️ Доброе утро! Сегодня твоя норма: {goal} мл. Погода: {weather}",
            "🌅 С добрым утром! Готов начать день с воды? Норма: {goal} мл",
            "⭐ Новый день - новые возможности! Твоя норма: {goal} мл",
            "☀️ Проснись и пей! Сегодня нужно выпить {goal} мл воды"
        ],
        "en": [
            "☀️ Good morning! Today's goal: {goal} ml. Weather: {weather}",
            "🌅 Good morning! Ready to start the day with water? Goal: {goal} ml",
            "⭐ New day - new opportunities! Your goal: {goal} ml",
            "☀️ Wake up and drink! Today you need {goal} ml of water"
        ]
    },
    "evening": {
        "ru": [
            "🌙 Итоги дня: выпито {current} из {goal} мл ({percent}%)",
            "📊 Сегодня ты выпил(а) {current} мл воды. {message}",
            "⭐ Дневная статистика: {current} мл. Завтра будет лучше!",
            "🌙 Отличный день! Выпито {current} мл. Отдыхай и набирайся сил!"
        ],
        "en": [
            "🌙 Daily summary: {current} of {goal} ml ({percent}%)",
            "📊 Today you drank {current} ml of water. {message}",
            "⭐ Daily stats: {current} ml. Tomorrow will be even better!",
            "🌙 Great day! You drank {current} ml. Rest and recharge!"
        ]
    }
}

# Success messages for goal completion
GOAL_COMPLETION_MESSAGES = {
    "ru": [
        "🎉 Поздравляю! Ты выполнил(а) дневную норму!",
        "🌟 Отлично! Цель достигнута! Ты молодец!",
        "💪 Ура! Норма выполнена! Так держать!",
        "🏆 Ты справился(ась) с нормой! Горжусь тобой!",
        "✨ Ещё один успешный день! Норма выполнена!"
    ],
    "en": [
        "🎉 Congratulations! You've reached your daily goal!",
        "🌟 Great job! Goal achieved! Well done!",
        "💪 Hooray! Goal completed! Keep it up!",
        "🏆 You did it! I'm proud of you!",
        "✨ Another successful day! Goal completed!"
    ]
}

# Reminder intervals for different times of day
TIME_BASED_INTERVALS = {
    "morning": 45,      # утром чаще (каждые 45 мин)
    "afternoon": 60,    # днём стандартно (каждый час)
    "evening": 90,      # вечером реже (каждые 1.5 часа)
    "night": 120        # ночью ещё реже (каждые 2 часа)
}