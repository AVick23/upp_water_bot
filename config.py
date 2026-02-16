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
                    if key not in os.environ:
                        os.environ[key] = value

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
    
    DEFAULT_NOTIFICATION_START: int = 8
    DEFAULT_NOTIFICATION_END: int = 22
    NOTIFICATION_INTERVAL_HOURS: int = 2
    MIN_DAILY_WATER_ML: int = 1000
    MAX_DAILY_WATER_ML: int = 5000
    MAX_CUSTOM_FAVORITES: int = 5
    STREAK_RESET_HOUR: int = 6

config = Config()

# ============================================================================
# ENUMS
# ============================================================================

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class ActivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ActivityMode(str, Enum):
    NORMAL = "normal"
    WORKOUT = "workout"
    FOCUS = "focus"
    VACATION = "vacation"

class DrinkType(str, Enum):
    # ВОДА
    WATER = "water"
    SPARKLING_WATER = "sparkling"
    MINERAL_WATER = "mineral"
    # ЧАЙ
    TEA_BLACK = "tea_black"
    TEA_GREEN = "tea_green"
    TEA_HERBAL = "tea_herbal"
    TEA_WITH_MILK = "tea_milk"
    MATCHA = "matcha"
    # КОФЕ
    ESPRESSO = "espresso"
    AMERICANO = "americano"
    CAPPUCCINO = "cappuccino"
    LATTE = "latte"
    FLAT_WHITE = "flat_white"
    MOCHA = "mocha"
    ICED_COFFEE = "iced_coffee"
    COLD_BREW = "cold_brew"
    # ДРУГИЕ
    JUICE = "juice"
    SMOOTHIE = "smoothie"
    MILK = "milk"
    SODA = "soda"
    ENERGY_DRINK = "energy"

class AchievementType(str, Enum):
    # Серии дней
    STREAK_3 = "streak_3"
    STREAK_7 = "streak_7"
    STREAK_14 = "streak_14"
    STREAK_21 = "streak_21"
    STREAK_30 = "streak_30"
    STREAK_50 = "streak_50"
    STREAK_100 = "streak_100"
    STREAK_200 = "streak_200"
    STREAK_365 = "streak_365"
    STREAK_500 = "streak_500"
    STREAK_1000 = "streak_1000"
    # Объём
    VOLUME_5L = "volume_5l"
    VOLUME_10L = "volume_10l"
    VOLUME_25L = "volume_25l"
    VOLUME_50L = "volume_50l"
    VOLUME_100L = "volume_100l"
    VOLUME_250L = "volume_250l"
    VOLUME_500L = "volume_500l"
    VOLUME_1000L = "volume_1000l"
    VOLUME_2500L = "volume_2500l"
    VOLUME_5000L = "volume_5000l"
    VOLUME_10000L = "volume_10000l"
    # Временные
    EARLY_BIRD = "early_bird"
    MORNING_HYDRATION = "morning_hydration"
    LUNCH_BREAK = "lunch_break"
    EVENING_CALM = "evening_calm"
    NIGHT_OWL = "night_owl"
    MIDNIGHT_SNACK = "midnight_snack"
    # Превышение нормы
    OVER_110 = "over_110"
    OVER_125 = "over_125"
    OVER_150 = "over_150"
    OVER_200 = "over_200"
    EXACT_NORM = "exact_norm"
    # Дни недели
    MONDAY_START = "monday_start"
    FRIDAY_VIBE = "friday_vibe"
    WEEKEND_HERO = "weekend_hero"
    FULL_WEEK = "full_week"
    # Сезонные
    WINTER_HYDRATION = "winter_hydration"
    SPRING_AWAKENING = "spring_awakening"
    SUMMER_HEAT = "summer_heat"
    AUTUMN_RAIN = "autumn_rain"
    NEW_YEAR = "new_year"
    # Особые
    FIRST_DAY = "first_day"
    FIRST_WEEK = "first_week"
    FIRST_MONTH = "first_month"
    COMEBACK = "comeback"
    TRAVELER = "traveler"
    VARIETY_KING = "variety_king"

# ============================================================================
# DRINK COEFFICIENTS
# ============================================================================

DRINK_COEFFICIENTS: Dict[DrinkType, float] = {
    # Вода
    DrinkType.WATER: 1.0,
    DrinkType.SPARKLING_WATER: 1.0,
    DrinkType.MINERAL_WATER: 1.0,
    # Чай
    DrinkType.TEA_BLACK: 0.9,
    DrinkType.TEA_GREEN: 0.95,
    DrinkType.TEA_HERBAL: 0.95,
    DrinkType.TEA_WITH_MILK: 0.85,
    DrinkType.MATCHA: 0.8,
    # Кофе
    DrinkType.ESPRESSO: 0.7,
    DrinkType.AMERICANO: 0.85,
    DrinkType.CAPPUCCINO: 0.75,
    DrinkType.LATTE: 0.7,
    DrinkType.FLAT_WHITE: 0.72,
    DrinkType.MOCHA: 0.65,
    DrinkType.ICED_COFFEE: 0.8,
    DrinkType.COLD_BREW: 0.9,
    # Другие
    DrinkType.JUICE: 0.7,
    DrinkType.SMOOTHIE: 0.75,
    DrinkType.MILK: 0.85,
    DrinkType.SODA: 0.5,
    DrinkType.ENERGY_DRINK: 0.4,
}

WATER_PRESETS: List[int] = [150, 250, 500, 1000]

# ============================================================================
# ACHIEVEMENTS DEFINITIONS
# ============================================================================

ACHIEVEMENTS = {
    # Серии
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
    # Объём
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
    AchievementType.VOLUME_10000L: {"emoji": "🔱", "xp": 10000, "rarity": "mythic"},
    # Временные
    AchievementType.EARLY_BIRD: {"emoji": "🐦", "xp": 75, "rarity": "uncommon"},
    AchievementType.MORNING_HYDRATION: {"emoji": "🌅", "xp": 100, "rarity": "uncommon"},
    AchievementType.LUNCH_BREAK: {"emoji": "🍽️", "xp": 50, "rarity": "common"},
    AchievementType.EVENING_CALM: {"emoji": "🌆", "xp": 50, "rarity": "common"},
    AchievementType.NIGHT_OWL: {"emoji": "🦉", "xp": 100, "rarity": "uncommon"},
    AchievementType.MIDNIGHT_SNACK: {"emoji": "🌙", "xp": 150, "rarity": "rare"},
    # Превышение
    AchievementType.OVER_110: {"emoji": "📈", "xp": 50, "rarity": "common"},
    AchievementType.OVER_125: {"emoji": "🚀", "xp": 100, "rarity": "uncommon"},
    AchievementType.OVER_150: {"emoji": "⚡", "xp": 200, "rarity": "rare"},
    AchievementType.OVER_200: {"emoji": "💥", "xp": 500, "rarity": "epic"},
    AchievementType.EXACT_NORM: {"emoji": "🎯", "xp": 150, "rarity": "rare"},
    # Дни недели
    AchievementType.MONDAY_START: {"emoji": "📆", "xp": 75, "rarity": "common"},
    AchievementType.FRIDAY_VIBE: {"emoji": "🎉", "xp": 75, "rarity": "common"},
    AchievementType.WEEKEND_HERO: {"emoji": "🦸", "xp": 100, "rarity": "uncommon"},
    AchievementType.FULL_WEEK: {"emoji": "🏆", "xp": 500, "rarity": "epic"},
    # Сезонные
    AchievementType.WINTER_HYDRATION: {"emoji": "❄️", "xp": 200, "rarity": "rare"},
    AchievementType.SPRING_AWAKENING: {"emoji": "🌸", "xp": 200, "rarity": "rare"},
    AchievementType.SUMMER_HEAT: {"emoji": "☀️", "xp": 200, "rarity": "rare"},
    AchievementType.AUTUMN_RAIN: {"emoji": "🍂", "xp": 200, "rarity": "rare"},
    AchievementType.NEW_YEAR: {"emoji": "🎄", "xp": 500, "rarity": "epic"},
    # Особые
    AchievementType.FIRST_DAY: {"emoji": "🎉", "xp": 50, "rarity": "common"},
    AchievementType.FIRST_WEEK: {"emoji": "⭐", "xp": 150, "rarity": "uncommon"},
    AchievementType.FIRST_MONTH: {"emoji": "🌟", "xp": 500, "rarity": "rare"},
    AchievementType.COMEBACK: {"emoji": "💪", "xp": 100, "rarity": "uncommon"},
    AchievementType.TRAVELER: {"emoji": "✈️", "xp": 300, "rarity": "epic"},
    AchievementType.VARIETY_KING: {"emoji": "👑", "xp": 200, "rarity": "rare"},
}

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
    RU = {
        # Welcome
        "welcome_title": "💧 Водный трекер",
        "welcome_text": "Привет! Я помогу тебе отслеживать потребление воды и поддерживать водный баланс.",
        "btn_start": "🚀 Начать",
        
        # Registration
        "reg_weight": "⚖️ Введи свой вес (кг)",
        "reg_weight_hint": "От 30 до 200 кг",
        "reg_height": "📏 Введи свой рост (см)",
        "reg_height_hint": "От 100 до 250 см",
        "reg_gender": "👤 Выбери пол",
        "reg_activity": "🏃 Уровень активности",
        "reg_city": "🏙️ Город (опционально)",
        "reg_city_hint": "Для погодной коррекции нормы воды",
        "reg_skip": "⏭️ Пропустить",
        "reg_complete": "🎉 Готово!",
        "reg_complete_text": "Настройка завершена! Твоя дневная норма: {norm} мл",
        
        # Main menu
        "main_today": "Сегодня",
        "main_add_water": "💧 Добавить напиток",
        "main_stats": "📈 Статистика",
        "main_settings": "⚙️ Настройки",
        "main_achievements": "🏆 Достижения",
        "main_about": "❓ О боте",
        
        # Add water
        "add_water_title": "💧 Сколько выпил?",
        "add_custom": "✏️ Свой объём",
        "add_success": "✅ Добавлено {volume} мл ({effective} эффективно)",
        "add_select_category": "Выберите тип напитка:",
        "add_select_drink": "Выберите напиток:",
        
        # Drink categories
        "cat_water": "💧 Вода",
        "cat_tea": "🍵 Чай",
        "cat_coffee": "☕ Кофе",
        "cat_other": "🥤 Другое",
        
        # Drinks - Water
        "drink_water": "💧 Вода",
        "drink_sparkling": "💫 Газированная",
        "drink_mineral": "🧂 Минеральная",
        # Drinks - Tea
        "drink_tea_black": "红茶 Чёрный чай",
        "drink_tea_green": "绿茶 Зелёный чай",
        "drink_tea_herbal": "🌿 Травяной чай",
        "drink_tea_milk": "🥛 Чай с молоком",
        "drink_matcha": "🍵 Матча",
        # Drinks - Coffee
        "drink_espresso": "☕ Эспрессо",
        "drink_americano": "☕ Американо",
        "drink_cappuccino": "☕ Капучино",
        "drink_latte": "☕ Латте",
        "drink_flat_white": "☕ Флэт уайт",
        "drink_mocha": "☕ Мокка",
        "drink_iced_coffee": "🧊 Айс кофе",
        "drink_cold_brew": "❄️ Колд брю",
        # Drinks - Other
        "drink_juice": "🧃 Сок",
        "drink_smoothie": "🥤 Смузи",
        "drink_milk": "🥛 Молоко",
        "drink_soda": "🥤 Газировка",
        "drink_energy": "⚡ Энергетик",
        
        # Statistics
        "stats_day": "📅 День",
        "stats_week": "📆 Неделя",
        "stats_month": "🗓️ Месяц",
        "stats_year": "📊 Год",
        "stats_total": "Всего",
        "stats_average": "В среднем",
        "stats_best_day": "Лучший день",
        "stats_streak": "🔥 Серия",
        "stats_days": "дней",
        
        # Settings
        "settings_profile": "👤 Профиль",
        "settings_notifications": "🔔 Уведомления",
        "settings_timezone": "🌍 Часовой пояс",
        "settings_mode": "🎭 Режим",
        "settings_language": "🌐 Язык",
        "settings_export": "📤 Экспорт данных",
        
        # Profile editing
        "profile_title": "👤 Мой профиль",
        "profile_edit": "✏️ Редактировать",
        "profile_weight": "⚖️ Вес",
        "profile_height": "📏 Рост",
        "profile_gender": "👤 Пол",
        "profile_activity": "🏃 Активность",
        "profile_city": "🏙️ Город",
        "profile_edit_weight": "Введите новый вес (30-200 кг):",
        "profile_edit_height": "Введите новый рост (100-250 см):",
        "profile_edit_city": "Введите город или 'del' для удаления:",
        "profile_updated": "✅ Профиль обновлён!",
        
        # Timezone
        "tz_select": "🌍 Выберите часовой пояс:",
        "tz_updated": "✅ Часовой пояс обновлён!",
        
        # Activity modes
        "mode_normal": "😊 Обычный",
        "mode_workout": "💪 Тренировка",
        "mode_focus": "🎯 Фокус",
        "mode_vacation": "🏖️ Отпуск",
        "mode_changed": "Режим изменён на: {mode}",
        
        # Activity levels
        "activity_low": "🐢 Низкая",
        "activity_medium": "🚶 Средняя",
        "activity_high": "🏃 Высокая",
        
        # Notifications
        "notif_morning": "☀️ Доброе утро! Погода: {weather}. Норма на сегодня: {norm} мл",
        "notif_reminder": "💧 Пора попить! Осталось выпить: {remaining} мл",
        "notif_evening": "🌙 Итог дня: {current} из {goal} мл ({percent}%)",
        "notif_achievement": "🎉 Новое достижение: {name}!",
        "notif_achievement_legendary": "🌟 ЛЕГЕНДАРНОЕ: {name}! 🌟",
        "notif_achievement_mythic": "💎 МИФИЧЕСКОЕ: {name}! 💎",
        "notif_level_up": "🎊 Уровень повышен! Теперь ты {level} уровня!",
        
        # Achievements names
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
        "ach_early_bird": "🐦 Ранняя пташка",
        "ach_morning_hydration": "🌅 Утренний заряд",
        "ach_lunch_break": "🍽️ Обеденный перерыв",
        "ach_evening_calm": "🌆 Вечернее спокойствие",
        "ach_night_owl": "🦉 Ночная сова",
        "ach_midnight_snack": "🌙 Полуночный глоток",
        "ach_over_110": "📈 Чуть больше",
        "ach_over_125": "🚀 Сверх нормы",
        "ach_over_150": "⚡ Полтора норматива",
        "ach_over_200": "💥 Двойная норма!",
        "ach_exact_norm": "🎯 Точность — вежливость",
        "ach_monday_start": "📆 Понедельник — день тяжёлый?",
        "ach_friday_vibe": "🎉 Пятничное настроение",
        "ach_weekend_hero": "🦸 Выходной герой",
        "ach_full_week": "🏆 Идеальная неделя",
        "ach_winter_hydration": "❄️ Зимняя гидратация",
        "ach_spring_awakening": "🌸 Весеннее пробуждение",
        "ach_summer_heat": "☀️ Летняя жара",
        "ach_autumn_rain": "🍂 Осенний дождь",
        "ach_new_year": "🎄 Новогодний глоток",
        "ach_first_day": "🎉 Первый день",
        "ach_first_week": "⭐ Первая неделя",
        "ach_first_month": "🌟 Первый месяц",
        "ach_comeback": "💪 Возвращение героя",
        "ach_traveler": "✈️ Путешественник",
        "ach_variety_king": "👑 Король разнообразия",
        
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
        
        # Errors
        "error_invalid_number": "❌ Введи корректное число",
        "error_range_weight": "❌ Вес должен быть от 30 до 200 кг",
        "error_range_height": "❌ Рост должен быть от 100 до 250 см",
        "error_unknown": "❌ Что-то пошло не так. Попробуй ещё раз.",
        
        # Buttons
        "btn_back": "◀️ Назад",
        "btn_cancel": "❌ Отмена",
        "btn_confirm": "✅ Подтвердить",
        "btn_male": "👨 Мужской",
        "btn_female": "👩 Женский",
        
        # Export
        "export_csv": "📊 CSV",
        "export_json": "📋 JSON",
        "export_success": "📤 Данные экспортированы",
    }
    
    EN = {
        # Welcome
        "welcome_title": "💧 Water Tracker",
        "welcome_text": "Hi! I'll help you track water intake and maintain hydration.",
        "btn_start": "🚀 Start",
        
        # Registration
        "reg_weight": "⚖️ Enter your weight (kg)",
        "reg_weight_hint": "From 30 to 200 kg",
        "reg_height": "📏 Enter your height (cm)",
        "reg_height_hint": "From 100 to 250 cm",
        "reg_gender": "👤 Select gender",
        "reg_activity": "🏃 Activity level",
        "reg_city": "🏙️ City (optional)",
        "reg_city_hint": "For weather-based water norm adjustment",
        "reg_skip": "⏭️ Skip",
        "reg_complete": "🎉 Done!",
        "reg_complete_text": "Setup complete! Your daily goal: {norm} ml",
        
        # Main menu
        "main_today": "Today",
        "main_add_water": "💧 Add drink",
        "main_stats": "📈 Statistics",
        "main_settings": "⚙️ Settings",
        "main_achievements": "🏆 Achievements",
        "main_about": "❓ About",
        
        # Add water
        "add_water_title": "💧 How much?",
        "add_custom": "✏️ Custom",
        "add_success": "✅ Added {volume} ml ({effective} effective)",
        "add_select_category": "Select drink type:",
        "add_select_drink": "Select drink:",
        
        # Drink categories
        "cat_water": "💧 Water",
        "cat_tea": "🍵 Tea",
        "cat_coffee": "☕ Coffee",
        "cat_other": "🥤 Other",
        
        # Drinks - Water
        "drink_water": "💧 Water",
        "drink_sparkling": "💫 Sparkling",
        "drink_mineral": "🧂 Mineral",
        # Drinks - Tea
        "drink_tea_black": "🫖 Black Tea",
        "drink_tea_green": "🍵 Green Tea",
        "drink_tea_herbal": "🌿 Herbal Tea",
        "drink_tea_milk": "🥛 Milk Tea",
        "drink_matcha": "🍵 Matcha",
        # Drinks - Coffee
        "drink_espresso": "☕ Espresso",
        "drink_americano": "☕ Americano",
        "drink_cappuccino": "☕ Cappuccino",
        "drink_latte": "☕ Latte",
        "drink_flat_white": "☕ Flat White",
        "drink_mocha": "☕ Mocha",
        "drink_iced_coffee": "🧊 Iced Coffee",
        "drink_cold_brew": "❄️ Cold Brew",
        # Drinks - Other
        "drink_juice": "🧃 Juice",
        "drink_smoothie": "🥤 Smoothie",
        "drink_milk": "🥛 Milk",
        "drink_soda": "🥤 Soda",
        "drink_energy": "⚡ Energy Drink",
        
        # Statistics
        "stats_day": "📅 Day",
        "stats_week": "📆 Week",
        "stats_month": "🗓️ Month",
        "stats_year": "📊 Year",
        "stats_total": "Total",
        "stats_average": "Average",
        "stats_best_day": "Best day",
        "stats_streak": "🔥 Streak",
        "stats_days": "days",
        
        # Settings
        "settings_profile": "👤 Profile",
        "settings_notifications": "🔔 Notifications",
        "settings_timezone": "🌍 Timezone",
        "settings_mode": "🎭 Mode",
        "settings_language": "🌐 Language",
        "settings_export": "📤 Export data",
        
        # Profile editing
        "profile_title": "👤 My Profile",
        "profile_edit": "✏️ Edit",
        "profile_weight": "⚖️ Weight",
        "profile_height": "📏 Height",
        "profile_gender": "👤 Gender",
        "profile_activity": "🏃 Activity",
        "profile_city": "🏙️ City",
        "profile_edit_weight": "Enter new weight (30-200 kg):",
        "profile_edit_height": "Enter new height (100-250 cm):",
        "profile_edit_city": "Enter city or 'del' to remove:",
        "profile_updated": "✅ Profile updated!",
        
        # Timezone
        "tz_select": "🌍 Select your timezone:",
        "tz_updated": "✅ Timezone updated!",
        
        # Activity modes
        "mode_normal": "😊 Normal",
        "mode_workout": "💪 Workout",
        "mode_focus": "🎯 Focus",
        "mode_vacation": "🏖️ Vacation",
        "mode_changed": "Mode changed to: {mode}",
        
        # Activity levels
        "activity_low": "🐢 Low",
        "activity_medium": "🚶 Medium",
        "activity_high": "🏃 High",
        
        # Notifications
        "notif_morning": "☀️ Good morning! Weather: {weather}. Daily goal: {norm} ml",
        "notif_reminder": "💧 Time to hydrate! Remaining: {remaining} ml",
        "notif_evening": "🌙 Daily summary: {current} of {goal} ml ({percent}%)",
        "notif_achievement": "🎉 New achievement: {name}!",
        "notif_achievement_legendary": "🌟 LEGENDARY: {name}! 🌟",
        "notif_achievement_mythic": "💎 MYTHIC: {name}! 💎",
        "notif_level_up": "🎊 Level up! You're now level {level}!",
        
        # Achievements names (same as RU but translated)
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
        "ach_early_bird": "🐦 Early Bird",
        "ach_morning_hydration": "🌅 Morning Charge",
        "ach_lunch_break": "🍽️ Lunch Break",
        "ach_evening_calm": "🌆 Evening Calm",
        "ach_night_owl": "🦉 Night Owl",
        "ach_midnight_snack": "🌙 Midnight Sip",
        "ach_over_110": "📈 A Bit More",
        "ach_over_125": "🚀 Above Goal",
        "ach_over_150": "⚡ One and a Half",
        "ach_over_200": "💥 Double Goal!",
        "ach_exact_norm": "🎯 Precision",
        "ach_monday_start": "📆 Monday Starter",
        "ach_friday_vibe": "🎉 Friday Vibes",
        "ach_weekend_hero": "🦸 Weekend Hero",
        "ach_full_week": "🏆 Perfect Week",
        "ach_winter_hydration": "❄️ Winter Hydration",
        "ach_spring_awakening": "🌸 Spring Awakening",
        "ach_summer_heat": "☀️ Summer Heat",
        "ach_autumn_rain": "🍂 Autumn Rain",
        "ach_new_year": "🎄 New Year Sip",
        "ach_first_day": "🎉 First Day",
        "ach_first_week": "⭐ First Week",
        "ach_first_month": "🌟 First Month",
        "ach_comeback": "💪 Hero's Return",
        "ach_traveler": "✈️ Traveler",
        "ach_variety_king": "👑 Variety King",
        
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
        
        # Errors
        "error_invalid_number": "❌ Enter a valid number",
        "error_range_weight": "❌ Weight must be 30-200 kg",
        "error_range_height": "❌ Height must be 100-250 cm",
        "error_unknown": "❌ Something went wrong. Try again.",
        
        # Buttons
        "btn_back": "◀️ Back",
        "btn_cancel": "❌ Cancel",
        "btn_confirm": "✅ Confirm",
        "btn_male": "👨 Male",
        "btn_female": "👩 Female",
        
        # Export
        "export_csv": "📊 CSV",
        "export_json": "📋 JSON",
        "export_success": "📤 Data exported",
    }
    
    @classmethod
    def get(cls, key: str, lang: str = "ru") -> str:
        strings = cls.RU if lang.lower() == "ru" else cls.EN
        return strings.get(key, key)


def get_user_locale(lang_code: str) -> str:
    if lang_code and lang_code.lower().startswith("ru"):
        return "ru"
    return "en"


# ============================================================================
# KEYBOARDS
# ============================================================================

def get_main_keyboard(lang: str = "ru"):
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


def get_water_keyboard(lang: str = "ru"):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [
            InlineKeyboardButton(f"💧 {preset} мл" if lang == "ru" else f"💧 {preset} ml", callback_data=f"water_{preset}")
            for preset in WATER_PRESETS[:2]
        ],
        [
            InlineKeyboardButton(f"💧 {preset} мл" if lang == "ru" else f"💧 {preset} ml", callback_data=f"water_{preset}")
            for preset in WATER_PRESETS[2:]
        ],
        [
            InlineKeyboardButton(Locale.get("add_custom", lang), callback_data="water_custom"),
            InlineKeyboardButton(Locale.get("btn_cancel", lang), callback_data="cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_drink_category_keyboard(lang: str = "ru"):
    """Клавиатура выбора категории напитка"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton(Locale.get("cat_water", lang), callback_data="cat_water")],
        [InlineKeyboardButton(Locale.get("cat_tea", lang), callback_data="cat_tea")],
        [InlineKeyboardButton(Locale.get("cat_coffee", lang), callback_data="cat_coffee")],
        [InlineKeyboardButton(Locale.get("cat_other", lang), callback_data="cat_other")],
        [InlineKeyboardButton(Locale.get("btn_cancel", lang), callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_drink_type_keyboard(lang: str = "ru", category: str = "water"):
    """Клавиатура выбора конкретного напитка"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    drinks_map = {
        "water": [DrinkType.WATER, DrinkType.SPARKLING_WATER, DrinkType.MINERAL_WATER],
        "tea": [DrinkType.TEA_BLACK, DrinkType.TEA_GREEN, DrinkType.TEA_HERBAL, DrinkType.TEA_WITH_MILK, DrinkType.MATCHA],
        "coffee": [DrinkType.ESPRESSO, DrinkType.AMERICANO, DrinkType.CAPPUCCINO, DrinkType.LATTE, DrinkType.FLAT_WHITE, DrinkType.MOCHA, DrinkType.ICED_COFFEE, DrinkType.COLD_BREW],
        "other": [DrinkType.JUICE, DrinkType.SMOOTHIE, DrinkType.MILK, DrinkType.SODA, DrinkType.ENERGY_DRINK],
    }
    
    keyboard = []
    row = []
    for i, drink in enumerate(drinks_map.get(category, [])):
        name = Locale.get(f"drink_{drink.value}", lang)
        row.append(InlineKeyboardButton(name, callback_data=f"drink_{drink.value}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="drink_cat")])
    
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard(lang: str = "ru"):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton(Locale.get("settings_profile", lang), callback_data="settings_profile")],
        [InlineKeyboardButton(Locale.get("settings_notifications", lang), callback_data="settings_notifications")],
        [InlineKeyboardButton(Locale.get("settings_timezone", lang), callback_data="settings_timezone")],
        [InlineKeyboardButton(Locale.get("settings_mode", lang), callback_data="settings_mode")],
        [InlineKeyboardButton(Locale.get("settings_language", lang), callback_data="settings_language")],
        [InlineKeyboardButton(Locale.get("settings_export", lang), callback_data="settings_export")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_profile_keyboard(lang: str = "ru"):
    """Клавиатура редактирования профиля"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [
            InlineKeyboardButton(Locale.get("profile_weight", lang), callback_data="edit_weight"),
            InlineKeyboardButton(Locale.get("profile_height", lang), callback_data="edit_height"),
        ],
        [
            InlineKeyboardButton(Locale.get("profile_gender", lang), callback_data="edit_gender"),
            InlineKeyboardButton(Locale.get("profile_activity", lang), callback_data="edit_activity"),
        ],
        [InlineKeyboardButton(Locale.get("profile_city", lang), callback_data="edit_city")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_mode_keyboard(lang: str = "ru", current_mode: str = "normal"):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    def mode_btn(mode: ActivityMode, label_key: str):
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
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский" + (" ✓" if lang == "ru" else ""), callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English" + (" ✓" if lang == "en" else ""), callback_data="lang_en")],
        [InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_export_keyboard(lang: str = "ru"):
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
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [
            InlineKeyboardButton(Locale.get("btn_male", lang), callback_data=f"gender_{Gender.MALE.value}"),
            InlineKeyboardButton(Locale.get("btn_female", lang), callback_data=f"gender_{Gender.FEMALE.value}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_activity_keyboard(lang: str = "ru"):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton(Locale.get("activity_low", lang), callback_data=f"activity_{ActivityLevel.LOW.value}")],
        [InlineKeyboardButton(Locale.get("activity_medium", lang), callback_data=f"activity_{ActivityLevel.MEDIUM.value}")],
        [InlineKeyboardButton(Locale.get("activity_high", lang), callback_data=f"activity_{ActivityLevel.HIGH.value}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(lang: str = "ru", callback_data: str = "main_menu"):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [[InlineKeyboardButton(Locale.get("btn_back", lang), callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)


def get_timezone_keyboard(lang: str = "ru"):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    # Список популярных часовых поясов
    timezones = [
        ("UTC-12:00", "Etc/GMT+12"),
        ("UTC-11:00", "Etc/GMT+11"),
        ("UTC-10:00", "Pacific/Honolulu"),
        ("UTC-09:00", "America/Anchorage"),
        ("UTC-08:00", "America/Los_Angeles"),
        ("UTC-07:00", "America/Denver"),
        ("UTC-06:00", "America/Chicago"),
        ("UTC-05:00", "America/New_York"),
        ("UTC-04:00", "America/Caracas"),
        ("UTC-03:00", "America/Sao_Paulo"),
        ("UTC-02:00", "Etc/GMT+2"),
        ("UTC-01:00", "Atlantic/Azores"),
        ("UTC+00:00", "UTC"),
        ("UTC+01:00", "Europe/London"),
        ("UTC+02:00", "Europe/Berlin"),
        ("UTC+03:00", "Europe/Moscow"),
        ("UTC+04:00", "Europe/Samara"),
        ("UTC+05:00", "Asia/Yekaterinburg"),
        ("UTC+06:00", "Asia/Almaty"),
        ("UTC+07:00", "Asia/Bangkok"),
        ("UTC+08:00", "Asia/Singapore"),
        ("UTC+09:00", "Asia/Tokyo"),
        ("UTC+10:00", "Australia/Sydney"),
        ("UTC+11:00", "Pacific/Noumea"),
        ("UTC+12:00", "Pacific/Auckland"),
    ]

    keyboard = []
    row = []
    for label, tz_name in timezones:
        row.append(InlineKeyboardButton(label, callback_data=f"tz_{tz_name}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings")])
    
    return InlineKeyboardMarkup(keyboard)