"""
Constants for achievements module
"""

from config import AchievementType, ACHIEVEMENTS, RARITY_COLORS

# Achievement categories for organization
ACHIEVEMENT_CATEGORIES = {
    "streak": {
        "name_ru": "🔥 Серии",
        "name_en": "🔥 Streaks",
        "icon": "🔥",
        "types": [
            AchievementType.STREAK_3,
            AchievementType.STREAK_7,
            AchievementType.STREAK_14,
            AchievementType.STREAK_21,
            AchievementType.STREAK_30,
            AchievementType.STREAK_50,
            AchievementType.STREAK_100,
            AchievementType.STREAK_200,
            AchievementType.STREAK_365,
            AchievementType.STREAK_500,
            AchievementType.STREAK_1000,
        ]
    },
    "volume": {
        "name_ru": "💧 Объём",
        "name_en": "💧 Volume",
        "icon": "💧",
        "types": [
            AchievementType.VOLUME_5L,
            AchievementType.VOLUME_10L,
            AchievementType.VOLUME_25L,
            AchievementType.VOLUME_50L,
            AchievementType.VOLUME_100L,
            AchievementType.VOLUME_250L,
            AchievementType.VOLUME_500L,
            AchievementType.VOLUME_1000L,
            AchievementType.VOLUME_2500L,
            AchievementType.VOLUME_5000L,
            AchievementType.VOLUME_10000L,
        ]
    },
    "time": {
        "name_ru": "⏰ Время",
        "name_en": "⏰ Time",
        "icon": "⏰",
        "types": [
            AchievementType.EARLY_BIRD,
            AchievementType.MORNING_HYDRATION,
            AchievementType.LUNCH_BREAK,
            AchievementType.EVENING_CALM,
            AchievementType.NIGHT_OWL,
            AchievementType.MIDNIGHT_SNACK,
        ]
    },
    "overachievement": {
        "name_ru": "⚡ Превышение",
        "name_en": "⚡ Overachievement",
        "icon": "⚡",
        "types": [
            AchievementType.OVER_110,
            AchievementType.OVER_125,
            AchievementType.OVER_150,
            AchievementType.OVER_200,
            AchievementType.EXACT_NORM,
        ]
    },
    "weekday": {
        "name_ru": "📅 Дни недели",
        "name_en": "📅 Weekdays",
        "icon": "📅",
        "types": [
            AchievementType.MONDAY_START,
            AchievementType.FRIDAY_VIBE,
            AchievementType.WEEKEND_HERO,
            AchievementType.FULL_WEEK,
        ]
    },
    "seasonal": {
        "name_ru": "🌸 Сезонные",
        "name_en": "🌸 Seasonal",
        "icon": "🌸",
        "types": [
            AchievementType.WINTER_HYDRATION,
            AchievementType.SPRING_AWAKENING,
            AchievementType.SUMMER_HEAT,
            AchievementType.AUTUMN_RAIN,
            AchievementType.NEW_YEAR,
        ]
    },
    "special": {
        "name_ru": "✨ Особые",
        "name_en": "✨ Special",
        "icon": "✨",
        "types": [
            AchievementType.FIRST_DAY,
            AchievementType.FIRST_WEEK,
            AchievementType.FIRST_MONTH,
            AchievementType.COMEBACK,
            AchievementType.TRAVELER,
            AchievementType.VARIETY_KING,
        ]
    }
}

# Rarity display information
RARITY_DISPLAY = {
    "common": {
        "name_ru": "Обычное",
        "name_en": "Common",
        "emoji": "⚪",
        "color": "#808080",
        "order": 1
    },
    "uncommon": {
        "name_ru": "Необычное",
        "name_en": "Uncommon",
        "emoji": "🟢",
        "color": "#00FF00",
        "order": 2
    },
    "rare": {
        "name_ru": "Редкое",
        "name_en": "Rare",
        "emoji": "🔵",
        "color": "#0000FF",
        "order": 3
    },
    "epic": {
        "name_ru": "Эпическое",
        "name_en": "Epic",
        "emoji": "🟣",
        "color": "#800080",
        "order": 4
    },
    "legendary": {
        "name_ru": "Легендарное",
        "name_en": "Legendary",
        "emoji": "🟡",
        "color": "#FFD700",
        "order": 5
    },
    "mythic": {
        "name_ru": "Мифическое",
        "name_en": "Mythic",
        "emoji": "🔴",
        "color": "#FF0000",
        "order": 6
    }
}

# Achievement progress thresholds
PROGRESS_THRESHOLDS = {
    AchievementType.STREAK_3: 3,
    AchievementType.STREAK_7: 7,
    AchievementType.STREAK_14: 14,
    AchievementType.STREAK_21: 21,
    AchievementType.STREAK_30: 30,
    AchievementType.STREAK_50: 50,
    AchievementType.STREAK_100: 100,
    AchievementType.STREAK_200: 200,
    AchievementType.STREAK_365: 365,
    AchievementType.STREAK_500: 500,
    AchievementType.STREAK_1000: 1000,
    AchievementType.VOLUME_5L: 5000,
    AchievementType.VOLUME_10L: 10000,
    AchievementType.VOLUME_25L: 25000,
    AchievementType.VOLUME_50L: 50000,
    AchievementType.VOLUME_100L: 100000,
    AchievementType.VOLUME_250L: 250000,
    AchievementType.VOLUME_500L: 500000,
    AchievementType.VOLUME_1000L: 1000000,
    AchievementType.VOLUME_2500L: 2500000,
    AchievementType.VOLUME_5000L: 5000000,
    AchievementType.VOLUME_10000L: 10000000,
}

# Achievement unlock messages
UNLOCK_MESSAGES = {
    "ru": {
        "title": "🏆 ПОЛУЧЕНО ДОСТИЖЕНИЕ!",
        "new": "✨ Новое достижение!",
        "congrats": "Поздравляем!",
        "share": "📢 Поделиться",
        "view_all": "👀 Все достижения",
        "next": "🎯 Следующее: {name}",
        "progress": "📊 Прогресс: {current}/{target} ({percent}%)",
    },
    "en": {
        "title": "🏆 ACHIEVEMENT UNLOCKED!",
        "new": "✨ New achievement!",
        "congrats": "Congratulations!",
        "share": "📢 Share",
        "view_all": "👀 View all",
        "next": "🎯 Next: {name}",
        "progress": "📊 Progress: {current}/{target} ({percent}%)",
    }
}

# Achievement stats messages
STATS_MESSAGES = {
    "ru": {
        "title": "🏆 Достижения",
        "total": "Всего: {count}",
        "by_rarity": "По редкости:",
        "recent": "📅 Последние:",
        "missing": "❌ Не получено: {count}",
        "completion": "📊 Завершено: {percent}%",
        "total_xp": "✨ Всего XP: {xp}",
        "level": "⭐ Уровень: {level}",
    },
    "en": {
        "title": "🏆 Achievements",
        "total": "Total: {count}",
        "by_rarity": "By rarity:",
        "recent": "📅 Recent:",
        "missing": "❌ Missing: {count}",
        "completion": "📊 Completion: {percent}%",
        "total_xp": "✨ Total XP: {xp}",
        "level": "⭐ Level: {level}",
    }
}