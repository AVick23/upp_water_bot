"""
Water tracking module for WaterBot
Handles all drink logging functionality
"""

from telegram.ext import CallbackQueryHandler, MessageHandler, filters

from water.handlers import (
    cb_add_water,
    cb_water_volume,
    cb_drink_category,
    cb_drink_type,
    handle_custom_volume,
    cb_add_favorite,
    cb_quick_add
)
from water.keyboards import (
    get_water_keyboard,
    get_drink_category_keyboard,
    get_drink_type_keyboard,
    get_quick_add_keyboard,
    get_notification_keyboard
)
from water.utils import (
    format_success_message,
    validate_custom_volume,
    get_available_volumes,
    calculate_effective_volume
)
from water.constants import (
    WATER_PRESETS,
    DRINK_CATEGORIES,
    DRINK_NAMES,
    SUCCESS_MESSAGES
)
from common.decorators import require_registration


def register_handlers(application):
    """Register all water-related handlers"""
    
    # Main add water handler
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_add_water),
            pattern="^add_water$"
        )
    )
    
    # Volume selection
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_water_volume),
            pattern="^water_"
        )
    )
    
    # Category selection
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_drink_category),
            pattern="^cat_|^drink_cat$"
        )
    )
    
    # Drink type selection
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_drink_type),
            pattern="^drink_"
        )
    )
    
    # Favorite handling
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_add_favorite),
            pattern="^fav_"
        )
    )
    
    # Quick add
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_quick_add),
            pattern="^quick_"
        )
    )
    
    # Custom volume input
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_custom_volume
        )
    )


__all__ = [
    # Registration function
    'register_handlers',
    
    # Keyboards
    'get_water_keyboard',
    'get_drink_category_keyboard',
    'get_drink_type_keyboard',
    'get_quick_add_keyboard',
    'get_notification_keyboard',
    
    # Utilities
    'format_success_message',
    'validate_custom_volume',
    'get_available_volumes',
    'calculate_effective_volume',
    
    # Constants
    'WATER_PRESETS',
    'DRINK_CATEGORIES',
    'DRINK_NAMES',
    'SUCCESS_MESSAGES'
]