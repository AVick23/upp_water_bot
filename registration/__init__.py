"""
Registration module for WaterBot
Handles user onboarding and profile management
"""

from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters, ConversationHandler

from registration.handlers import (
    start_registration,
    show_profile,
    update_gender_activity,
    get_registration_conversation_handler,
    get_profile_edit_handlers
)
from registration.keyboards import (
    get_start_keyboard,
    get_gender_keyboard,
    get_activity_keyboard,
    get_city_keyboard,
    get_profile_edit_keyboard
)
from registration.states import (
    STATE_START, STATE_WEIGHT, STATE_HEIGHT, STATE_GENDER,
    STATE_ACTIVITY, STATE_CITY, STATE_EDIT_WEIGHT,
    STATE_EDIT_HEIGHT, STATE_EDIT_CITY
)
from registration.utils import (
    validate_weight,
    validate_height,
    validate_city,
    get_user_locale,
    format_registration_complete,
    calculate_user_norm
)
from common.decorators import require_registration


def register_handlers(application):
    """Register all registration-related handlers"""
    
    # Add registration conversation handler
    registration_handler = get_registration_conversation_handler()
    application.add_handler(registration_handler)
    
    # Add profile edit conversation handler
    profile_edit_handler = get_profile_edit_handlers()
    application.add_handler(profile_edit_handler)
    
    # Add profile view handler
    application.add_handler(
        CallbackQueryHandler(
            require_registration(show_profile),
            pattern="^settings_profile$"
        )
    )
    
    # Add gender/activity update handlers
    application.add_handler(
        CallbackQueryHandler(
            require_registration(update_gender_activity),
            pattern="^(gender_|activity_)"
        )
    )


__all__ = [
    # Registration function
    "register_handlers",
    
    # Handlers
    "start_registration",
    "show_profile",
    "update_gender_activity",
    "get_registration_conversation_handler",
    "get_profile_edit_handlers",
    
    # Keyboards
    "get_start_keyboard",
    "get_gender_keyboard",
    "get_activity_keyboard",
    "get_city_keyboard",
    "get_profile_edit_keyboard",
    
    # States
    "STATE_START",
    "STATE_WEIGHT",
    "STATE_HEIGHT",
    "STATE_GENDER",
    "STATE_ACTIVITY",
    "STATE_CITY",
    "STATE_EDIT_WEIGHT",
    "STATE_EDIT_HEIGHT",
    "STATE_EDIT_CITY",
    
    # Utils
    "validate_weight",
    "validate_height",
    "validate_city",
    "get_user_locale",
    "format_registration_complete",
    "calculate_user_norm",
]