"""
Settings module for WaterBot
Handles all user settings and preferences
"""

from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ConversationHandler

from settings.handlers import (
    # Main settings
    cb_settings,
    cb_settings_profile,
    cb_settings_timezone,
    cb_settings_mode,
    cb_settings_language,
    cb_settings_export,
    cb_settings_danger,
    
    # Timezone
    cb_set_timezone,
    cb_timezone_auto,
    
    # Mode
    cb_set_mode,
    
    # Language
    cb_set_language,
    
    # Export
    cb_export_data,
    
    # Danger zone
    cb_danger_action,
    cb_confirm_action,
    cb_cancel_action,
)

# Импортируем обработчики уведомлений из модуля notifications
from notifications.handlers import (
    cb_settings_notifications,
    cb_toggle_notifications,
    cb_notification_presets,
    cb_set_notification_preset,
    cb_set_notif_time,
    cb_time_hour_range,
    cb_time_hour,
    cb_time_set,
    cb_time_now,
    cb_time_custom,
    handle_custom_time_input
)

from settings.keyboards import (
    get_settings_main_keyboard,
    get_profile_settings_keyboard,
    get_notifications_settings_keyboard,
    get_notification_presets_keyboard,
    get_time_picker_keyboard,
    get_minute_picker_keyboard,
    get_timezone_keyboard,
    get_mode_keyboard,
    get_language_keyboard,
    get_export_keyboard,
    get_danger_zone_keyboard,
    get_confirmation_keyboard
)
from settings.utils import (
    get_user_settings_display,
    format_settings_summary,
    validate_time_format,
    get_timezone_by_offset,
    get_mode_multiplier,
    get_language_name
)
from settings.constants import (
    SETTINGS_CATEGORIES,
    TIMEZONE_PRESETS,
    LANGUAGES,
    NOTIFICATION_PRESETS,
    MODE_DESCRIPTIONS,
    MODE_MULTIPLIERS,
    DANGER_ACTIONS
)
from common.decorators import require_registration
from registration.handlers import show_profile, update_gender_activity


def register_handlers(application):
    """Register all settings-related handlers"""
    
    # Main settings menu
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_settings),
            pattern="^settings$"
        )
    )
    
    # Profile settings
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_settings_profile),
            pattern="^settings_profile$"
        )
    )
    
    # Notification settings - ИСПРАВЛЕНО: используем обработчики из notifications
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_settings_notifications),
            pattern="^settings_notifications$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_toggle_notifications),
            pattern="^toggle_notifications$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_notification_presets),
            pattern="^notif_presets$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_set_notification_preset),
            pattern="^notif_preset_"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_set_notif_time),
            pattern="^set_notif_"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_time_hour_range),
            pattern="^time_hour_range_"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_time_hour),
            pattern="^time_hour_"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_time_set),
            pattern="^time_set_"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_time_now),
            pattern="^time_now_"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_time_custom),
            pattern="^time_custom_"
        )
    )
    
    # Timezone settings
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_settings_timezone),
            pattern="^settings_timezone$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_set_timezone),
            pattern="^tz_set_"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_timezone_auto),
            pattern="^tz_auto$"
        )
    )
    
    # Mode settings
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_settings_mode),
            pattern="^settings_mode$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_set_mode),
            pattern="^mode_set_"
        )
    )
    
    # Language settings
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_settings_language),
            pattern="^settings_language$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_set_language),
            pattern="^lang_set_"
        )
    )
    
    # Export settings
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_settings_export),
            pattern="^settings_export$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_export_data),
            pattern="^export_(csv|json)$"
        )
    )
    
    # Danger zone
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_settings_danger),
            pattern="^settings_danger$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_danger_action),
            pattern="^danger_"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_confirm_action),
            pattern="^confirm_"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_cancel_action),
            pattern="^cancel_"
        )
    )
    
    # Custom time input handler
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_custom_time_input
        )
    )


__all__ = [
    # Registration
    'register_handlers',
    
    # Keyboards
    'get_settings_main_keyboard',
    'get_profile_settings_keyboard',
    'get_notifications_settings_keyboard',
    'get_notification_presets_keyboard',
    'get_time_picker_keyboard',
    'get_minute_picker_keyboard',
    'get_timezone_keyboard',
    'get_mode_keyboard',
    'get_language_keyboard',
    'get_export_keyboard',
    'get_danger_zone_keyboard',
    'get_confirmation_keyboard',
    
    # Utilities
    'get_user_settings_display',
    'format_settings_summary',
    'validate_time_format',
    'get_timezone_by_offset',
    'get_mode_multiplier',
    'get_language_name',
    
    # Constants
    'SETTINGS_CATEGORIES',
    'TIMEZONE_PRESETS',
    'LANGUAGES',
    'NOTIFICATION_PRESETS',
    'MODE_DESCRIPTIONS',
    'MODE_MULTIPLIERS',
    'DANGER_ACTIONS'
]