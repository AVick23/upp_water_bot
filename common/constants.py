"""
Common constants and shared values
"""

from enum import Enum
from typing import Dict, Any

# Bot information
BOT_INFO = {
    "name": "WaterBot",
    "version": "2.0.0",
    "description": "Smart water tracking bot",
    "author": "Your Name",
    "year": 2024
}

# Message length limits
MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024

# Pagination
ITEMS_PER_PAGE = 10
BUTTONS_PER_ROW = 2

# Cache TTL (seconds)
CACHE_TTL = {
    "user": 300,  # 5 minutes
    "weather": 1800,  # 30 minutes
    "stats": 600,  # 10 minutes
    "leaderboard": 300,  # 5 minutes
}

# Rate limiting
RATE_LIMITS = {
    "messages_per_second": 30,
    "callback_per_second": 30,
    "commands_per_minute": 20,
}

# Error messages
ERROR_MESSAGES = {
    "ru": {
        "unknown": "❌ Произошла неизвестная ошибка. Попробуйте позже.",
        "timeout": "⏰ Время ожидания истекло. Попробуйте снова.",
        "not_found": "🔍 Запрошенный ресурс не найден.",
        "forbidden": "⛔ У вас нет прав для этого действия.",
        "rate_limit": "🐢 Слишком много запросов. Подождите немного.",
        "maintenance": "🛠️ Бот на техническом обслуживании. Скоро вернемся!",
        "invalid_input": "❌ Неверный формат ввода. Проверьте и попробуйте снова.",
        "user_not_found": "👤 Пользователь не найден.",
        "db_error": "💾 Ошибка базы данных. Администратор уже уведомлен.",
    },
    "en": {
        "unknown": "❌ An unknown error occurred. Try again later.",
        "timeout": "⏰ Timeout expired. Please try again.",
        "not_found": "🔍 Requested resource not found.",
        "forbidden": "⛔ You don't have permission for this action.",
        "rate_limit": "🐢 Too many requests. Please wait.",
        "maintenance": "🛠️ Bot is under maintenance. Be right back!",
        "invalid_input": "❌ Invalid input format. Check and try again.",
        "user_not_found": "👤 User not found.",
        "db_error": "💾 Database error. Admin has been notified.",
    }
}

# Success messages
SUCCESS_MESSAGES = {
    "ru": {
        "saved": "✅ Изменения сохранены!",
        "deleted": "🗑️ Запись удалена!",
        "sent": "📨 Отправлено!",
        "updated": "🔄 Обновлено!",
        "completed": "🎉 Завершено!",
    },
    "en": {
        "saved": "✅ Changes saved!",
        "deleted": "🗑️ Record deleted!",
        "sent": "📨 Sent!",
        "updated": "🔄 Updated!",
        "completed": "🎉 Completed!",
    }
}

# Loading animations
LOADING_ANIMATIONS = [
    "⏳",
    "⌛",
    "🔄",
    "⏳",
    "⌛",
]

# Progress bar symbols
PROGRESS_SYMBOLS = {
    "empty": "░",
    "quarter": "▒",
    "half": "▓",
    "full": "█",
    "start": "╭",
    "end": "╮",
    "fill": "─",
}

# Time formats
TIME_FORMATS = {
    "full": "%Y-%m-%d %H:%M:%S",
    "date": "%Y-%m-%d",
    "time": "%H:%M",
    "datetime": "%d.%m.%Y %H:%M",
    "short_date": "%d.%m.%y",
    "month_year": "%B %Y",
    "weekday": "%A",
}

# Emoji mapping
EMOJI_MAP = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "question": "❓",
    "wait": "⏳",
    "done": "🎉",
    "water": "💧",
    "fire": "🔥",
    "star": "⭐",
    "trophy": "🏆",
    "medal": "🏅",
    "crown": "👑",
    "heart": "❤️",
    "clock": "⏰",
    "calendar": "📅",
    "settings": "⚙️",
    "stats": "📊",
    "back": "◀️",
    "forward": "▶️",
    "up": "⬆️",
    "down": "⬇️",
    "left": "⬅️",
    "right": "➡️",
    "check": "✅",
    "cross": "❌",
    "plus": "➕",
    "minus": "➖",
    "edit": "✏️",
    "delete": "🗑️",
    "share": "📢",
    "copy": "📋",
    "link": "🔗",
    "lock": "🔒",
    "unlock": "🔓",
    "bell": "🔔",
    "mute": "🔕",
    "email": "📧",
    "phone": "📱",
    "home": "🏠",
    "work": "💼",
    "school": "🎓",
    "gym": "💪",
    "coffee": "☕",
    "tea": "🍵",
    "juice": "🧃",
    "food": "🍽️",
}

# Button callbacks
CALLBACK_PATTERNS = {
    "main_menu": "^main_menu$",
    "back": "^back_",
    "cancel": "^cancel$",
    "confirm": "^confirm_",
    "page": "^page_",
    "refresh": "^refresh$",
    "help": "^help$",
    "info": "^info$",
}

# HTTP status codes
HTTP_STATUS = {
    "ok": 200,
    "created": 201,
    "bad_request": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "too_many_requests": 429,
    "server_error": 500,
}

# Log levels
LOG_LEVELS = {
    "debug": 10,
    "info": 20,
    "warning": 30,
    "error": 40,
    "critical": 50,
}

# Database error codes
DB_ERROR_CODES = {
    "unique_violation": "23505",
    "foreign_key_violation": "23503",
    "not_null_violation": "23502",
    "check_violation": "23514",
}