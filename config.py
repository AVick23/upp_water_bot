"""
Configuration, constants and localization for WaterBot
Telegram Bot "Вода за день" - Apple-level Design & Experience
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List
from pathlib import Path

# ============================================================================
# LOAD .ENV FILE
# ============================================================================

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value

# Load .env before creating config
load_env_file()

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

@dataclass
class Config:
    """Main configuration class"""
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///waterbot.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Notification settings
    DEFAULT_NOTIFICATION_START: int = 8  # 08:00
    DEFAULT_NOTIFICATION_END: int = 22   # 22:00
    NOTIFICATION_INTERVAL_HOURS: int = 2
    
    # Water calculation defaults
    MIN_DAILY_WATER_ML: int = 1000
    MAX_DAILY_WATER_ML: int = 5000
    
    # Limits
    MAX_CUSTOM_FAVORITES: int = 5
    STREAK_RESET_HOUR: int = 6  # Reset streak at 6 AM

config = Config()

# ============================================================================
# ENUMS
# ============================================================================

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class ActivityLevel(str, Enum):
    LOW = "low"        # Office work, minimal exercise
    MEDIUM = "medium"  # Regular exercise 2-3 times/week
    HIGH = "high"      # Daily exercise or physical work

class ActivityMode(str, Enum):
    NORMAL = "normal"
    WORKOUT = "workout"    # Increased norm, more frequent notifications
    FOCUS = "focus"        # Minimal notifications
    VACATION = "vacation"  # Reduced norm

class DrinkType(str, Enum):
    WATER = "water"       # coefficient 1.0
    TEA = "tea"           # coefficient 0.9
    COFFEE = "coffee"     # coefficient 0.8
    JUICE = "juice"       # coefficient 0.7
    SODA = "soda"         # coefficient 0.5

class AchievementType(str, Enum):
    # === СЕРИИ ДНЕЙ (Streaks) ===
    STREAK_3 = "streak_3"           # 3 дня подряд
    STREAK_7 = "streak_7"           # 7 дней подряд (неделя)
    STREAK_14 = "streak_14"         # 14 дней подряд (2 недели)
    STREAK_21 = "streak_21"         # 21 день (привычка)
    STREAK_30 = "streak_30"         # 30 дней (месяц)
    STREAK_50 = "streak_50"         # 50 дней
    STREAK_100 = "streak_100"       # 100 дней
    STREAK_200 = "streak_200"       # 200 дней
    STREAK_365 = "streak_365"       # 365 дней (год!)
    STREAK_500 = "streak_500"       # 500 дней (легенда)
    STREAK_1000 = "streak_1000"     # 1000 дней (мастер)
    
    # === ОБЪЁМНЫЕ (Volume) ===
    VOLUME_5L = "volume_5l"         # 5 литров
    VOLUME_10L = "volume_10l"       # 10 литров (ведро)
    VOLUME_25L = "volume_25l"       # 25 литров
    VOLUME_50L = "volume_50l"       # 50 литров
    VOLUME_100L = "volume_100l"     # 100 литров (бассейн)
    VOLUME_250L = "volume_250l"     # 250 литров
    VOLUME_500L = "volume_500l"     # 500 литров
    VOLUME_1000L = "volume_1000l"   # 1000 литров (озеро)
    VOLUME_2500L = "volume_2500l"   # 2500 литров
    VOLUME_5000L = "volume_5000l"   # 5000 литров (море)
    VOLUME_10000L = "volume_10000l" # 10000 литров (океан)
    
    # === ВРЕМЕННЫЕ (Time-based) ===
    EARLY_BIRD = "early_bird"       # До 8 утра
    MORNING_HYDRATION = "morning_hydration"   # Выпить 500мл до 10 утра
    LUNCH_BREAK = "lunch_break"     # Выпить в обед (12-14)
    EVENING_CALM = "evening_calm"   # Выпить вечером (18-21)
    NIGHT_OWL = "night_owl"         # Выпить после 23:00
    MIDNIGHT_SNACK = "midnight_snack"  # Выпить между 00:00 и 05:00
    
    # === ПРЕВЫШЕНИЕ НОРМЫ (Overachievement) ===
    OVER_110 = "over_110"           # 110% от нормы
    OVER_125 = "over_125"           # 125% от нормы
    OVER_150 = "over_150"           # 150% от нормы
    OVER_200 = "over_200"           # 200% от нормы (двойная норма!)
    EXACT_NORM = "exact_norm"       # Точно 100% (±50мл)
    
    # === ПО НАПИТКАМ (Drink Types) ===
    WATER_PURIST = "water_purist"   # Только вода 30 дней
    TEA_LOVER = "tea_lover"         # 100 чашек чая
    COFFEE_FAN = "coffee_fan"       # 100 чашек кофе
    JUICE_FAN = "juice_fan"         # 100 стаканов сока
    VARIETY_KING = "variety_king"   # Все 5 типов напитков за день
    
    # === ДНИ НЕДЕЛИ (Week Days) ===
    MONDAY_START = "monday_start"   # Выполнить норму в понедельник
    FRIDAY_VIBE = "friday_vibe"     # Выполнить норму в пятницу
    WEEKEND_HERO = "weekend_hero"   # Выполнить норму в выходные
    FULL_WEEK = "full_week"         # Выполнить норму все 7 дней недели
    
    # === СТАБИЛЬНОСТЬ (Consistency) ===
    CONSISTENT_7 = "consistent_7"   # 7 дней подряд ≥80% нормы
    CONSISTENT_30 = "consistent_30" # 30 дней подряд ≥80% нормы
    
    # === СЕЗОННЫЕ (Seasonal) ===
    WINTER_HYDRATION = "winter_hydration"  # Зимой
    SPRING_AWAKENING = "spring_awakening"  # Весной
    SUMMER_HEAT = "summer_heat"            # Летом
    AUTUMN_RAIN = "autumn_rain"            # Осенью
    NEW_YEAR = "new_year"          # 1 января
    
    # === ОСОБЫЕ (Special) ===
    FIRST_DAY = "first_day"         # Первый день
    FIRST_WEEK = "first_week"       # Первая неделя
    FIRST_MONTH = "first_month"     # Первый месяц
    COMEBACK = "comeback"           # Возврат после перерыва
    TRAVELER = "traveler"           # 10 разных часовых поясов
    
    # === СЕКРЕТНЫЕ (Secret) ===
    SECRET_MIDNIGHT = "secret_midnight"    # Полночь + 1 января
    SECRET_BIRTHDAY = "secret_birthday"    # День рождения (нужна дата)
    SECRET_SPEED = "secret_speed"          # Выпить 1л за 10 минут
    SECRET_PATIENCE = "secret_patience"    # 50 мл каждые 30 минут весь день

# ============================================================================
# DRINK COEFFICIENTS
# ============================================================================

DRINK_COEFFICIENTS: Dict[DrinkType, float] = {
    DrinkType.WATER: 1.0,
    DrinkType.TEA: 0.9,
    DrinkType.COFFEE: 0.8,
    DrinkType.JUICE: 0.7,
    DrinkType.SODA: 0.5,
}

# ============================================================================
# WATER PRESETS (ml)
# ============================================================================

WATER_PRESETS: List[int] = [150, 250, 500, 1000]

# ============================================================================
# ACHIEVEMENTS DEFINITIONS
# ============================================================================

ACHIEVEMENTS = {
    # === СЕРИИ ДНЕЙ ===
    AchievementType.STREAK_3: {"emoji": "🌱", "xp": 30, "rarity": "common"},
    AchievementType.STREAK_7: {"emoji": "🔥", "xp": 100, "rarity": "common"},
    AchievementType.STREAK_14: {"emoji": "⭐", "xp": 250, "rarity": "uncommon"},
    AchievementType.STREAK_21: {"emoji": "🎯", "xp": 400, "rarity": "uncommon"},
    AchievementType.STREAK_30: {"emoji": "💪", "xp": 500, "rarity": "rare"},
    AchievementType.STREAK_50: {"emoji": "🌟", "xp": 800, "rarity": "rare"},
    AchievementType.STREAK_100: {"emoji": "🏆", "xp": 2000, "rarity": "epic"},
    AchievementType.STREAK_200: {"emoji": "💎", "xp": 5000, "rarity": "epic"},
    AchievementType.STREAK_365: {"emoji": "👑", "xp": 10000, "rarity": "legendary"},
    AchievementType.STREAK_500: {"emoji": "🌈", "xp": 20000, "rarity": "legendary"},
    AchievementType.STREAK_1000: {"emoji": "🔯", "xp": 50000, "rarity": "mythic"},
    
    # === ОБЪЁМНЫЕ ===
    AchievementType.VOLUME_5L: {"emoji": "🥤", "xp": 25, "rarity": "common"},
    AchievementType.VOLUME_10L: {"emoji": "🪣", "xp": 50, "rarity": "common"},
    AchievementType.VOLUME_25L: {"emoji": "🧊", "xp": 100, "rarity": "uncommon"},
    AchievementType.VOLUME_50L: {"emoji": "🛁", "xp": 150, "rarity": "uncommon"},
    AchievementType.VOLUME_100L: {"emoji": "🏊", "xp": 300, "rarity": "rare"},
    AchievementType.VOLUME_250L: {"emoji": "🌊", "xp": 500, "rarity": "rare"},
    AchievementType.VOLUME_500L: {"emoji": "🏞️", "xp": 800, "rarity": "epic"},
    AchievementType.VOLUME_1000L: {"emoji": "🌌", "xp": 1500, "rarity": "epic"},
    AchievementType.VOLUME_2500L: {"emoji": "🌊", "xp": 3000, "rarity": "legendary"},
    AchievementType.VOLUME_5000L: {"emoji": "⛵", "xp": 5000, "rarity": "legendary"},
    AchievementType.VOLUME_10000L: {"emoji": "🌊🔱", "xp": 10000, "rarity": "mythic"},
    
    # === ВРЕМЕННЫЕ ===
    AchievementType.EARLY_BIRD: {"emoji": "🐦", "xp": 75, "rarity": "uncommon"},
    AchievementType.MORNING_HYDRATION: {"emoji": "🌅", "xp": 100, "rarity": "uncommon"},
    AchievementType.LUNCH_BREAK: {"emoji": "🍽️", "xp": 50, "rarity": "common"},
    AchievementType.EVENING_CALM: {"emoji": "🌆", "xp": 50, "rarity": "common"},
    AchievementType.NIGHT_OWL: {"emoji": "🦉", "xp": 100, "rarity": "uncommon"},
    AchievementType.MIDNIGHT_SNACK: {"emoji": "🌙", "xp": 150, "rarity": "rare"},
    
    # === ПРЕВЫШЕНИЕ НОРМЫ ===
    AchievementType.OVER_110: {"emoji": "📈", "xp": 50, "rarity": "common"},
    AchievementType.OVER_125: {"emoji": "🚀", "xp": 100, "rarity": "uncommon"},
    AchievementType.OVER_150: {"emoji": "⚡", "xp": 200, "rarity": "rare"},
    AchievementType.OVER_200: {"emoji": "💥", "xp": 500, "rarity": "epic"},
    AchievementType.EXACT_NORM: {"emoji": "🎯", "xp": 150, "rarity": "rare"},
    
    # === ПО НАПИТКАМ ===
    AchievementType.WATER_PURIST: {"emoji": "💧", "xp": 500, "rarity": "epic"},
    AchievementType.TEA_LOVER: {"emoji": "🍵", "xp": 200, "rarity": "rare"},
    AchievementType.COFFEE_FAN: {"emoji": "☕", "xp": 200, "rarity": "rare"},
    AchievementType.JUICE_FAN: {"emoji": "🧃", "xp": 200, "rarity": "rare"},
    AchievementType.VARIETY_KING: {"emoji": "🍹", "xp": 300, "rarity": "epic"},
    
    # === ДНИ НЕДЕЛИ ===
    AchievementType.MONDAY_START: {"emoji": "📆", "xp": 75, "rarity": "common"},
    AchievementType.FRIDAY_VIBE: {"emoji": "🎉", "xp": 75, "rarity": "common"},
    AchievementType.WEEKEND_HERO: {"emoji": "🦸", "xp": 100, "rarity": "uncommon"},
    AchievementType.FULL_WEEK: {"emoji": "🏆", "xp": 500, "rarity": "epic"},
    
    # === СТАБИЛЬНОСТЬ ===
    AchievementType.CONSISTENT_7: {"emoji": "📊", "xp": 200, "rarity": "rare"},
    AchievementType.CONSISTENT_30: {"emoji": "📈", "xp": 1000, "rarity": "legendary"},
    
    # === СЕЗОННЫЕ ===
    AchievementType.WINTER_HYDRATION: {"emoji": "❄️", "xp": 200, "rarity": "rare"},
    AchievementType.SPRING_AWAKENING: {"emoji": "🌸", "xp": 200, "rarity": "rare"},
    AchievementType.SUMMER_HEAT: {"emoji": "☀️", "xp": 200, "rarity": "rare"},
    AchievementType.AUTUMN_RAIN: {"emoji": "🍂", "xp": 200, "rarity": "rare"},
    AchievementType.NEW_YEAR: {"emoji": "🎄", "xp": 500, "rarity": "epic"},
    
    # === ОСОБЫЕ ===
    AchievementType.FIRST_DAY: {"emoji": "🎉", "xp": 50, "rarity": "common"},
    AchievementType.FIRST_WEEK: {"emoji": "⭐", "xp": 150, "rarity": "uncommon"},
    AchievementType.FIRST_MONTH: {"emoji": "🌟", "xp": 500, "rarity": "rare"},
    AchievementType.COMEBACK: {"emoji": "💪", "xp": 100, "rarity": "uncommon"},
    AchievementType.TRAVELER: {"emoji": "✈️", "xp": 300, "rarity": "epic"},
    
    # === СЕКРЕТНЫЕ ===
    AchievementType.SECRET_MIDNIGHT: {"emoji": "🔮", "xp": 1000, "rarity": "mythic"},
    AchievementType.SECRET_BIRTHDAY: {"emoji": "🎂", "xp": 500, "rarity": "legendary"},
    AchievementType.SECRET_SPEED: {"emoji": "⚡", "xp": 300, "rarity": "epic"},
    AchievementType.SECRET_PATIENCE: {"emoji": "🧘", "xp": 1000, "rarity": "legendary"},
}

# Редкость достижений для красивого отображения
RARITY_COLORS = {
    "common": "⚪",
    "uncommon": "🟢", 
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟡",
    "mythic": "🔴",
}

# ============================================================================
# LOCALIZATION
# ============================================================================

class Locale:
    """Localization strings for Russian and English"""
    
    RU = {
        # Onboarding
        "welcome_title": "💧 Водный трекер",
        "welcome_text": "Привет! Я помогу тебе отслеживать потребление воды и поддерживать водный баланс.",
        "btn_start": "🚀 Начать",
        
        # Registration steps
        "reg_weight": "⚖️ Введи свой вес (кг)",
        "reg_weight_hint": "От 30 до 200 кг",
        "reg_height": "📏 Введи свой рост (см)",
        "reg_height_hint": "От 100 до 250 см",
        "reg_gender": "👤 Выбери пол",
        "reg_activity": "🏃 Уровень активности",
        "reg_timezone": "🌍 Часовой пояс",
        "reg_timezone_detected": "Определён автоматически:",
        "reg_notification_time": "⏰ Время уведомлений",
        "reg_notification_hint": "С какого по какое время присылать напоминания?",
        "reg_city": "🏙️ Город (опционально)",
        "reg_city_hint": "Для погодной коррекции нормы воды",
        "reg_skip": "⏭️ Пропустить",
        "reg_complete": "🎉 Готово!",
        "reg_complete_text": "Настройка завершена! Твоя дневная норма: {norm} мл",
        
        # Main menu
        "main_progress": "📊 Прогресс за сегодня",
        "main_today": "Сегодня",
        "main_goal": "Цель",
        "main_add_water": "💧 Добавить воду",
        "main_stats": "📈 Статистика",
        "main_settings": "⚙️ Настройки",
        "main_achievements": "🏆 Достижения",
        "main_about": "❓ О боте",
        
        # Add water
        "add_water_title": "💧 Сколько выпил?",
        "add_custom": "✏️ Свой объём",
        "add_favorite": "⭐ Избранное",
        "add_success": "✅ Добавлено {volume} мл",
        "add_drink_type": "Что это?",
        
        # Quick actions
        "quick_ml": "{volume} мл",
        
        # Statistics
        "stats_day": "📅 День",
        "stats_week": "📆 Неделя",
        "stats_month": "🗓️ Месяц",
        "stats_year": "📊 Год",
        "stats_total": "Всего за период",
        "stats_average": "В среднем в день",
        "stats_best_day": "Лучший день",
        "stats_streak": "🔥 Серия",
        "stats_days": "дней",
        
        # Settings
        "settings_profile": "👤 Профиль",
        "settings_notifications": "🔔 Уведомления",
        "settings_mode": "🎭 Режим",
        "settings_language": "🌐 Язык",
        "settings_export": "📤 Экспорт данных",
        "settings_back": "◀️ Назад",
        
        # Activity modes
        "mode_normal": "😊 Обычный",
        "mode_workout": "💪 Тренировка",
        "mode_focus": "🎯 Фокус",
        "mode_vacation": "🏖️ Отпуск",
        "mode_changed": "Режим изменён на: {mode}",
        
        # Notifications
        "notif_morning": "☀️ Доброе утро! Погода: {weather}. Норма на сегодня: {norm} мл",
        "notif_reminder": "💧 Пора попить! Осталось выпить: {remaining} мл",
        "notif_evening": "🌙 Итог дня: {current} из {goal} мл ({percent}%)",
        "notif_streak_lost": "😔 Серия прервана. Начни заново!",
        "notif_achievement": "🎉 Новое достижение: {name}!",
        "notif_achievement_legendary": "🌟 ЛЕГЕНДАРНОЕ достижение: {name}! 🌟",
        "notif_achievement_mythic": "💎 МИФИЧЕСКОЕ достижение: {name}! 💎",
        "notif_level_up": "🎊 Уровень повышен! Теперь ты {level} уровня!",
        
        # Achievements - Серии дней
        "ach_streak_3": "🌱 Первые шаги",
        "ach_streak_7": "🔥 Неделя силы",
        "ach_streak_14": "⭐ Две недели подряд",
        "ach_streak_21": "🎯 Привычка сформирована",
        "ach_streak_30": "💪 Месяц дисциплины",
        "ach_streak_50": "🌟 Полёт нормальный",
        "ach_streak_100": "🏆 Водный мастер",
        "ach_streak_200": "💎 Дважды мастер",
        "ach_streak_365": "👑 Легенда года",
        "ach_streak_500": "🌈 Полубог гидратации",
        "ach_streak_1000": "🔯 Бог воды",
        
        # Achievements - Объёмные
        "ach_volume_5l": "🥤 Первый литраж",
        "ach_volume_10l": "🪣 Ведро",
        "ach_volume_25l": "🧊 Лёд воды",
        "ach_volume_50l": "🛁 Ванна",
        "ach_volume_100l": "🏊 Бассейн",
        "ach_volume_250l": "🌊 Волна",
        "ach_volume_500l": "🏞️ Пруд",
        "ach_volume_1000l": "🌌 Озеро",
        "ach_volume_2500l": "🌊 Море",
        "ach_volume_5000l": "⛵ Мореплаватель",
        "ach_volume_10000l": "🔱 Повелитель океана",
        
        # Achievements - Временные
        "ach_early_bird": "🐦 Ранняя пташка",
        "ach_morning_hydration": "🌅 Утренний заряд",
        "ach_lunch_break": "🍽️ Обеденный перерыв",
        "ach_evening_calm": "🌆 Вечернее спокойствие",
        "ach_night_owl": "🦉 Ночная сова",
        "ach_midnight_snack": "🌙 Полуночный глоток",
        
        # Achievements - Превышение нормы
        "ach_over_110": "📈 Чуть больше",
        "ach_over_125": "🚀 Сверх нормы",
        "ach_over_150": "⚡ Полтора норматива",
        "ach_over_200": "💥 Двойная норма!",
        "ach_exact_norm": "🎯 Точность — вежливость",
        
        # Achievements - По напиткам
        "ach_water_purist": "💧 Чистый вкус",
        "ach_tea_lover": "🍵 Чайный гурман",
        "ach_coffee_fan": "☕ Кофеман",
        "ach_juice_fan": "🧃 Любитель соков",
        "ach_variety_king": "🍹 Король разнообразия",
        
        # Achievements - Дни недели
        "ach_monday_start": "📆 Понедельник — день тяжёлый?",
        "ach_friday_vibe": "🎉 Пятничное настроение",
        "ach_weekend_hero": "🦸 Выходной герой",
        "ach_full_week": "🏆 Идеальная неделя",
        
        # Achievements - Стабильность
        "ach_consistent_7": "📊 Стабильная неделя",
        "ach_consistent_30": "📈 Месяц стабильности",
        
        # Achievements - Сезонные
        "ach_winter_hydration": "❄️ Зимняя гидратация",
        "ach_spring_awakening": "🌸 Весеннее пробуждение",
        "ach_summer_heat": "☀️ Летняя жара",
        "ach_autumn_rain": "🍂 Осенний дождь",
        "ach_new_year": "🎄 Новогодний глоток",
        
        # Achievements - Особые
        "ach_first_day": "🎉 Первый день",
        "ach_first_week": "⭐ Первая неделя",
        "ach_first_month": "🌟 Первый месяц",
        "ach_comeback": "💪 Возвращение героя",
        "ach_traveler": "✈️ Путешественник",
        
        # Achievements - Секретные
        "ach_secret_midnight": "🔮 Полуночный колдун",
        "ach_secret_birthday": "🎂 Именинник",
        "ach_secret_speed": "⚡ Скоростной глоток",
        "ach_secret_patience": "🧘 Мастер терпения",
        
        # Achievement categories
        "ach_category_streak": "🔥 Серии дней",
        "ach_category_volume": "💧 Объём",
        "ach_category_time": "⏰ Временные",
        "ach_category_drink": "🥤 Напитки",
        "ach_category_special": "⭐ Особые",
        "ach_category_secret": "🔮 Секретные",
        
        # Rarity
        "rarity_common": "⚪ Обычное",
        "rarity_uncommon": "🟢 Необычное",
        "rarity_rare": "🔵 Редкое",
        "rarity_epic": "🟣 Эпическое",
        "rarity_legendary": "🟡 Легендарное",
        "rarity_mythic": "🔴 Мифическое",
        
        # Motivation
        "motivation_great": "🌟 Отлично! Ты на верном пути!",
        "motivation_almost": "💪 Почти у цели! Осталось чуть-чуть!",
        "motivation_need_more": "💧 Время попить! Ты справишься!",
        "motivation_goal_reached": "🎉 Цель достигнута! Так держать!",
        "motivation_new_record": "🏆 Новый рекорд дня!",
        
        # Errors
        "error_invalid_number": "❌ Введи корректное число",
        "error_range_weight": "❌ Вес должен быть от 30 до 200 кг",
        "error_range_height": "❌ Рост должен быть от 100 до 250 см",
        "error_unknown": "❌ Что-то пошло не так. Попробуй ещё раз.",
        
        # Export
        "export_csv": "📊 CSV",
        "export_json": "📋 JSON",
        "export_success": "📤 Данные экспортированы",
        
        # Buttons
        "btn_back": "◀️ Назад",
        "btn_cancel": "❌ Отмена",
        "btn_confirm": "✅ Подтвердить",
        "btn_male": "👨 Мужской",
        "btn_female": "👩 Женский",
        
        # Activity levels
        "activity_low": "🐢 Низкая",
        "activity_medium": "🚶 Средняя", 
        "activity_high": "🏃 Высокая",
        
        # Drink types
        "drink_water": "💧 Вода",
        "drink_tea": "🍵 Чай",
        "drink_coffee": "☕ Кофе",
        "drink_juice": "🧃 Сок",
        "drink_soda": "🥤 Газировка",
    }
    
    EN = {
        # Onboarding
        "welcome_title": "💧 Water Tracker",
        "welcome_text": "Hi! I'll help you track water intake and maintain hydration.",
        "btn_start": "🚀 Start",
        
        # Registration steps
        "reg_weight": "⚖️ Enter your weight (kg)",
        "reg_weight_hint": "From 30 to 200 kg",
        "reg_height": "📏 Enter your height (cm)",
        "reg_height_hint": "From 100 to 250 cm",
        "reg_gender": "👤 Select gender",
        "reg_activity": "🏃 Activity level",
        "reg_timezone": "🌍 Timezone",
        "reg_timezone_detected": "Auto-detected:",
        "reg_notification_time": "⏰ Notification time",
        "reg_notification_hint": "When to send reminders?",
        "reg_city": "🏙️ City (optional)",
        "reg_city_hint": "For weather-based water norm adjustment",
        "reg_skip": "⏭️ Skip",
        "reg_complete": "🎉 Done!",
        "reg_complete_text": "Setup complete! Your daily goal: {norm} ml",
        
        # Main menu
        "main_progress": "📊 Today's progress",
        "main_today": "Today",
        "main_goal": "Goal",
        "main_add_water": "💧 Add water",
        "main_stats": "📈 Statistics",
        "main_settings": "⚙️ Settings",
        "main_achievements": "🏆 Achievements",
        "main_about": "❓ About",
        
        # Add water
        "add_water_title": "💧 How much?",
        "add_custom": "✏️ Custom",
        "add_favorite": "⭐ Favorites",
        "add_success": "✅ Added {volume} ml",
        "add_drink_type": "What is it?",
        
        # Quick actions
        "quick_ml": "{volume} ml",
        
        # Statistics
        "stats_day": "📅 Day",
        "stats_week": "📆 Week",
        "stats_month": "🗓️ Month",
        "stats_year": "📊 Year",
        "stats_total": "Total",
        "stats_average": "Average per day",
        "stats_best_day": "Best day",
        "stats_streak": "🔥 Streak",
        "stats_days": "days",
        
        # Settings
        "settings_profile": "👤 Profile",
        "settings_notifications": "🔔 Notifications",
        "settings_mode": "🎭 Mode",
        "settings_language": "🌐 Language",
        "settings_export": "📤 Export data",
        "settings_back": "◀️ Back",
        
        # Activity modes
        "mode_normal": "😊 Normal",
        "mode_workout": "💪 Workout",
        "mode_focus": "🎯 Focus",
        "mode_vacation": "🏖️ Vacation",
        "mode_changed": "Mode changed to: {mode}",
        
        # Notifications
        "notif_morning": "☀️ Good morning! Weather: {weather}. Daily goal: {norm} ml",
        "notif_reminder": "💧 Time to hydrate! Remaining: {remaining} ml",
        "notif_evening": "🌙 Daily summary: {current} of {goal} ml ({percent}%)",
        "notif_streak_lost": "😔 Streak lost. Start again!",
        "notif_achievement": "🎉 New achievement: {name}!",
        "notif_achievement_legendary": "🌟 LEGENDARY achievement: {name}! 🌟",
        "notif_achievement_mythic": "💎 MYTHIC achievement: {name}! 💎",
        "notif_level_up": "🎊 Level up! You're now level {level}!",
        
        # Achievements - Streaks
        "ach_streak_3": "🌱 First Steps",
        "ach_streak_7": "🔥 Week of Power",
        "ach_streak_14": "⭐ Two Weeks Running",
        "ach_streak_21": "🎯 Habit Formed",
        "ach_streak_30": "💪 Month of Discipline",
        "ach_streak_50": "🌟 On a Roll",
        "ach_streak_100": "🏆 Water Master",
        "ach_streak_200": "💎 Double Master",
        "ach_streak_365": "👑 Year Legend",
        "ach_streak_500": "🌈 Hydration Demigod",
        "ach_streak_1000": "🔯 Water God",
        
        # Achievements - Volume
        "ach_volume_5l": "🥤 First Literage",
        "ach_volume_10l": "🪣 Bucket",
        "ach_volume_25l": "🧊 Ice Cold",
        "ach_volume_50l": "🛁 Bathtub",
        "ach_volume_100l": "🏊 Pool",
        "ach_volume_250l": "🌊 Wave",
        "ach_volume_500l": "🏞️ Pond",
        "ach_volume_1000l": "🌌 Lake",
        "ach_volume_2500l": "🌊 Sea",
        "ach_volume_5000l": "⛵ Seafarer",
        "ach_volume_10000l": "🔱 Ocean Master",
        
        # Achievements - Time
        "ach_early_bird": "🐦 Early Bird",
        "ach_morning_hydration": "🌅 Morning Charge",
        "ach_lunch_break": "🍽️ Lunch Break",
        "ach_evening_calm": "🌆 Evening Calm",
        "ach_night_owl": "🦉 Night Owl",
        "ach_midnight_snack": "🌙 Midnight Sip",
        
        # Achievements - Overachievement
        "ach_over_110": "📈 A Bit More",
        "ach_over_125": "🚀 Above Goal",
        "ach_over_150": "⚡ One and a Half",
        "ach_over_200": "💥 Double Goal!",
        "ach_exact_norm": "🎯 Precision",
        
        # Achievements - Drinks
        "ach_water_purist": "💧 Pure Taste",
        "ach_tea_lover": "🍵 Tea Connoisseur",
        "ach_coffee_fan": "☕ Coffee Fan",
        "ach_juice_fan": "🧃 Juice Lover",
        "ach_variety_king": "🍹 Variety King",
        
        # Achievements - Week Days
        "ach_monday_start": "📆 Monday Starter",
        "ach_friday_vibe": "🎉 Friday Vibes",
        "ach_weekend_hero": "🦸 Weekend Hero",
        "ach_full_week": "🏆 Perfect Week",
        
        # Achievements - Consistency
        "ach_consistent_7": "📊 Consistent Week",
        "ach_consistent_30": "📈 Month of Consistency",
        
        # Achievements - Seasonal
        "ach_winter_hydration": "❄️ Winter Hydration",
        "ach_spring_awakening": "🌸 Spring Awakening",
        "ach_summer_heat": "☀️ Summer Heat",
        "ach_autumn_rain": "🍂 Autumn Rain",
        "ach_new_year": "🎄 New Year Sip",
        
        # Achievements - Special
        "ach_first_day": "🎉 First Day",
        "ach_first_week": "⭐ First Week",
        "ach_first_month": "🌟 First Month",
        "ach_comeback": "💪 Hero's Return",
        "ach_traveler": "✈️ Traveler",
        
        # Achievements - Secret
        "ach_secret_midnight": "🔮 Midnight Wizard",
        "ach_secret_birthday": "🎂 Birthday Star",
        "ach_secret_speed": "⚡ Speed Drinker",
        "ach_secret_patience": "🧘 Patience Master",
        
        # Achievement categories
        "ach_category_streak": "🔥 Streaks",
        "ach_category_volume": "💧 Volume",
        "ach_category_time": "⏰ Time-based",
        "ach_category_drink": "🥤 Drinks",
        "ach_category_special": "⭐ Special",
        "ach_category_secret": "🔮 Secret",
        
        # Rarity
        "rarity_common": "⚪ Common",
        "rarity_uncommon": "🟢 Uncommon",
        "rarity_rare": "🔵 Rare",
        "rarity_epic": "🟣 Epic",
        "rarity_legendary": "🟡 Legendary",
        "rarity_mythic": "🔴 Mythic",
        
        # Motivation
        "motivation_great": "🌟 Great! You're on track!",
        "motivation_almost": "💪 Almost there! Keep going!",
        "motivation_need_more": "💧 Time to drink! You got this!",
        "motivation_goal_reached": "🎉 Goal reached! Well done!",
        "motivation_new_record": "🏆 New daily record!",
        
        # Errors
        "error_invalid_number": "❌ Enter a valid number",
        "error_range_weight": "❌ Weight must be 30-200 kg",
        "error_range_height": "❌ Height must be 100-250 cm",
        "error_unknown": "❌ Something went wrong. Try again.",
        
        # Export
        "export_csv": "📊 CSV",
        "export_json": "📋 JSON",
        "export_success": "📤 Data exported",
        
        # Buttons
        "btn_back": "◀️ Back",
        "btn_cancel": "❌ Cancel",
        "btn_confirm": "✅ Confirm",
        "btn_male": "👨 Male",
        "btn_female": "👩 Female",
        
        # Activity levels
        "activity_low": "🐢 Low",
        "activity_medium": "🚶 Medium",
        "activity_high": "🏃 High",
        
        # Drink types
        "drink_water": "💧 Water",
        "drink_tea": "🍵 Tea",
        "drink_coffee": "☕ Coffee",
        "drink_juice": "🧃 Juice",
        "drink_soda": "🥤 Soda",
    }
    
    @classmethod
    def get(cls, key: str, lang: str = "ru") -> str:
        """Get localized string by key"""
        strings = cls.RU if lang.lower() == "ru" else cls.EN
        return strings.get(key, key)


def get_user_locale(lang_code: str) -> str:
    """Determine user locale from Telegram language code"""
    if lang_code and lang_code.lower().startswith("ru"):
        return "ru"
    return "en"


# ============================================================================
# KEYBOARD LAYOUTS (lazy import to avoid circular dependencies)
# ============================================================================

def get_water_keyboard(lang: str = "ru"):
    """Generate inline keyboard for water volume selection"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton(f"💧 {preset} мл" if lang == "ru" else f"💧 {preset} ml", 
                               callback_data=f"water_{preset}")
            for preset in WATER_PRESETS[:2]
        ],
        [
            InlineKeyboardButton(f"💧 {preset} мл" if lang == "ru" else f"💧 {preset} ml",
                               callback_data=f"water_{preset}")
            for preset in WATER_PRESETS[2:]
        ],
        [
            InlineKeyboardButton(Locale.get("add_custom", lang), callback_data="water_custom"),
            InlineKeyboardButton(Locale.get("btn_cancel", lang), callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_drink_type_keyboard(lang: str = "ru"):
    """Generate inline keyboard for drink type selection"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton(Locale.get("drink_water", lang), callback_data=f"drink_{DrinkType.WATER.value}"),
            InlineKeyboardButton(Locale.get("drink_tea", lang), callback_data=f"drink_{DrinkType.TEA.value}"),
        ],
        [
            InlineKeyboardButton(Locale.get("drink_coffee", lang), callback_data=f"drink_{DrinkType.COFFEE.value}"),
            InlineKeyboardButton(Locale.get("drink_juice", lang), callback_data=f"drink_{DrinkType.JUICE.value}"),
        ],
        [
            InlineKeyboardButton(Locale.get("drink_soda", lang), callback_data=f"drink_{DrinkType.SODA.value}"),
            InlineKeyboardButton(Locale.get("btn_cancel", lang), callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_keyboard(lang: str = "ru"):
    """Generate main menu inline keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton(Locale.get("main_add_water", lang), callback_data="add_water")],
        [
            InlineKeyboardButton(Locale.get("main_stats", lang), callback_data="stats"),
            InlineKeyboardButton(Locale.get("main_achievements", lang), callback_data="achievements"),
        ],
        [
            InlineKeyboardButton(Locale.get("main_settings", lang), callback_data="settings"),
            InlineKeyboardButton(Locale.get("main_about", lang), callback_data="about"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard(lang: str = "ru"):
    """Generate settings menu inline keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton(Locale.get("settings_profile", lang), callback_data="settings_profile")],
        [InlineKeyboardButton(Locale.get("settings_notifications", lang), callback_data="settings_notifications")],
        [InlineKeyboardButton(Locale.get("settings_mode", lang), callback_data="settings_mode")],
        [InlineKeyboardButton(Locale.get("settings_language", lang), callback_data="settings_language")],
        [InlineKeyboardButton(Locale.get("settings_export", lang), callback_data="settings_export")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_mode_keyboard(lang: str = "ru", current_mode: str = "normal"):
    """Generate activity mode selection keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    def mode_btn(mode: ActivityMode, label_key: str) -> InlineKeyboardButton:
        label = Locale.get(label_key, lang)
        if current_mode == mode.value:
            label = f"✓ {label}"
        return InlineKeyboardButton(label, callback_data=f"mode_{mode.value}")
    
    keyboard = [
        [mode_btn(ActivityMode.NORMAL, "mode_normal")],
        [mode_btn(ActivityMode.WORKOUT, "mode_workout")],
        [mode_btn(ActivityMode.FOCUS, "mode_focus")],
        [mode_btn(ActivityMode.VACATION, "mode_vacation")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_stats_keyboard(lang: str = "ru"):
    """Generate statistics period selection keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton(Locale.get("stats_day", lang), callback_data="stats_day"),
            InlineKeyboardButton(Locale.get("stats_week", lang), callback_data="stats_week"),
        ],
        [
            InlineKeyboardButton(Locale.get("stats_month", lang), callback_data="stats_month"),
            InlineKeyboardButton(Locale.get("stats_year", lang), callback_data="stats_year"),
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_language_keyboard(lang: str = "ru"):
    """Generate language selection keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский" + (" ✓" if lang == "ru" else ""), callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English" + (" ✓" if lang == "en" else ""), callback_data="lang_en")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_export_keyboard(lang: str = "ru"):
    """Generate export options keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton(Locale.get("export_csv", lang), callback_data="export_csv"),
            InlineKeyboardButton(Locale.get("export_json", lang), callback_data="export_json"),
        ],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_gender_keyboard(lang: str = "ru"):
    """Generate gender selection keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton(Locale.get("btn_male", lang), callback_data=f"gender_{Gender.MALE.value}"),
            InlineKeyboardButton(Locale.get("btn_female", lang), callback_data=f"gender_{Gender.FEMALE.value}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_activity_keyboard(lang: str = "ru"):
    """Generate activity level selection keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton(Locale.get("activity_low", lang), callback_data=f"activity_{ActivityLevel.LOW.value}")],
        [InlineKeyboardButton(Locale.get("activity_medium", lang), callback_data=f"activity_{ActivityLevel.MEDIUM.value}")],
        [InlineKeyboardButton(Locale.get("activity_high", lang), callback_data=f"activity_{ActivityLevel.HIGH.value}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(lang: str = "ru", callback_data: str = "main_menu"):
    """Generate simple back button keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [[InlineKeyboardButton(Locale.get("btn_back", lang), callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)