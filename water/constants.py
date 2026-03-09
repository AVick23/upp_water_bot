"""
Constants for water tracking module
"""

from config import DrinkType, DRINK_COEFFICIENTS

# Default volumes presets (ml)
WATER_PRESETS = [150, 250, 500, 1000]

# Category definitions
DRINK_CATEGORIES = {
    "water": {
        "name_ru": "💧 Вода",
        "name_en": "💧 Water",
        "drinks": [
            DrinkType.WATER,
            DrinkType.SPARKLING_WATER,
            DrinkType.MINERAL_WATER
        ]
    },
    "tea": {
        "name_ru": "🍵 Чай",
        "name_en": "🍵 Tea",
        "drinks": [
            DrinkType.TEA_BLACK,
            DrinkType.TEA_GREEN,
            DrinkType.TEA_HERBAL,
            DrinkType.TEA_WITH_MILK,
            DrinkType.MATCHA
        ]
    },
    "coffee": {
        "name_ru": "☕ Кофе",
        "name_en": "☕ Coffee",
        "drinks": [
            DrinkType.ESPRESSO,
            DrinkType.AMERICANO,
            DrinkType.CAPPUCCINO,
            DrinkType.LATTE,
            DrinkType.FLAT_WHITE,
            DrinkType.MOCHA,
            DrinkType.ICED_COFFEE,
            DrinkType.COLD_BREW
        ]
    },
    "other": {
        "name_ru": "🥤 Другое",
        "name_en": "🥤 Other",
        "drinks": [
            DrinkType.JUICE,
            DrinkType.SMOOTHIE,
            DrinkType.MILK,
            DrinkType.SODA,
            DrinkType.ENERGY_DRINK
        ]
    }
}

# Drink display names mapping
DRINK_NAMES = {
    # Water
    DrinkType.WATER: {"ru": "💧 Вода", "en": "💧 Water"},
    DrinkType.SPARKLING_WATER: {"ru": "💫 Газированная вода", "en": "💫 Sparkling water"},
    DrinkType.MINERAL_WATER: {"ru": "🧂 Минеральная вода", "en": "🧂 Mineral water"},
    
    # Tea
    DrinkType.TEA_BLACK: {"ru": "🫖 Чёрный чай", "en": "🫖 Black tea"},
    DrinkType.TEA_GREEN: {"ru": "🍵 Зелёный чай", "en": "🍵 Green tea"},
    DrinkType.TEA_HERBAL: {"ru": "🌿 Травяной чай", "en": "🌿 Herbal tea"},
    DrinkType.TEA_WITH_MILK: {"ru": "🥛 Чай с молоком", "en": "🥛 Milk tea"},
    DrinkType.MATCHA: {"ru": "🍵 Матча", "en": "🍵 Matcha"},
    
    # Coffee
    DrinkType.ESPRESSO: {"ru": "☕ Эспрессо", "en": "☕ Espresso"},
    DrinkType.AMERICANO: {"ru": "☕ Американо", "en": "☕ Americano"},
    DrinkType.CAPPUCCINO: {"ru": "☕ Капучино", "en": "☕ Cappuccino"},
    DrinkType.LATTE: {"ru": "☕ Латте", "en": "☕ Latte"},
    DrinkType.FLAT_WHITE: {"ru": "☕ Флэт уайт", "en": "☕ Flat white"},
    DrinkType.MOCHA: {"ru": "☕ Мокка", "en": "☕ Mocha"},
    DrinkType.ICED_COFFEE: {"ru": "🧊 Айс кофе", "en": "🧊 Iced coffee"},
    DrinkType.COLD_BREW: {"ru": "❄️ Колд брю", "en": "❄️ Cold brew"},
    
    # Other
    DrinkType.JUICE: {"ru": "🧃 Сок", "en": "🧃 Juice"},
    DrinkType.SMOOTHIE: {"ru": "🥤 Смузи", "en": "🥤 Smoothie"},
    DrinkType.MILK: {"ru": "🥛 Молоко", "en": "🥛 Milk"},
    DrinkType.SODA: {"ru": "🥤 Газировка", "en": "🥤 Soda"},
    DrinkType.ENERGY_DRINK: {"ru": "⚡ Энергетик", "en": "⚡ Energy drink"},
}

# Hydration coefficient display
COEFFICIENT_INFO = {
    "ru": "Коэффициент гидратации: {coeff}%",
    "en": "Hydration coefficient: {coeff}%"
}

# Success messages
SUCCESS_MESSAGES = {
    "ru": [
        "💧 Отлично! Вода — источник жизни!",
        "🌟 Ещё один шаг к здоровью!",
        "💪 Ты на верном пути!",
        "🌊 Так держать!",
        "🎯 Цель всё ближе!",
        "✨ Прекрасный выбор!",
        "🌈 Глоток свежести!",
        "⭐ Твоё тело скажет спасибо!"
    ],
    "en": [
        "💧 Great! Water is life!",
        "🌟 Another step to health!",
        "💪 You're on the right track!",
        "🌊 Keep it up!",
        "🎯 Getting closer to goal!",
        "✨ Excellent choice!",
        "🌈 Fresh sip!",
        "⭐ Your body will thank you!"
    ]
}

# Volume recommendations
VOLUME_RECOMMENDATIONS = {
    "small": {"ru": "Маленький глоток", "en": "Small sip"},
    "medium": {"ru": "Стандартный стакан", "en": "Standard glass"},
    "large": {"ru": "Большая кружка", "en": "Large mug"},
    "extra": {"ru": "Бутылка воды", "en": "Water bottle"}
}