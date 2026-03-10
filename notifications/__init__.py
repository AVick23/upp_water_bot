"""
Notifications module for WaterBot
Handles scheduled tasks, reminders, and notification management
"""

from notifications.jobs import register_jobs, job_minute_check, job_daily_reset
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
from notifications.keyboards import (
    get_notifications_settings_keyboard,
    get_notification_presets_keyboard,
    get_time_picker_keyboard,
    get_minute_picker_keyboard,
    get_notification_keyboard
)
from notifications.utils import (
    format_notification_time,
    calculate_next_notification_time,
    get_notification_preset,
    validate_notification_time,
    get_time_recommendation,
    is_time_in_window,
    clean_user_notification_data,
    format_notification_summary
)
from notifications.constants import (
    NOTIFICATION_PRESETS,
    NOTIFICATION_TYPES,
    NOTIFICATION_INTERVALS,
    TIME_PRESETS,
    NOTIFICATION_MESSAGES,
    GOAL_COMPLETION_MESSAGES,
    TIME_CATEGORIES
)


def register_handlers(application):
    """Register all notification-related handlers"""
    from telegram.ext import CallbackQueryHandler, MessageHandler, filters
    
    # Notification settings menu
    application.add_handler(
        CallbackQueryHandler(cb_settings_notifications, pattern="^settings_notifications$")
    )
    
    # Toggle notifications
    application.add_handler(
        CallbackQueryHandler(cb_toggle_notifications, pattern="^toggle_notifications$")
    )
    
    # Notification presets
    application.add_handler(
        CallbackQueryHandler(cb_notification_presets, pattern="^notif_presets$")
    )
    
    application.add_handler(
        CallbackQueryHandler(cb_set_notification_preset, pattern="^notif_preset_")
    )
    
    # Time selection
    application.add_handler(
        CallbackQueryHandler(cb_set_notif_time, pattern="^set_notif_")
    )
    
    application.add_handler(
        CallbackQueryHandler(cb_time_hour_range, pattern="^time_hour_range_")
    )
    
    application.add_handler(
        CallbackQueryHandler(cb_time_hour, pattern="^time_hour_")
    )
    
    application.add_handler(
        CallbackQueryHandler(cb_time_set, pattern="^time_set_")
    )
    
    application.add_handler(
        CallbackQueryHandler(cb_time_now, pattern="^time_now_")
    )
    
    application.add_handler(
        CallbackQueryHandler(cb_time_custom, pattern="^time_custom_")
    )
    
    # Custom time input
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_time_input)
    )


__all__ = [
    # Registration
    'register_handlers',
    'register_jobs',
    
    # Jobs
    'job_minute_check',
    'job_daily_reset',
    
    # Handlers
    'cb_settings_notifications',
    'cb_toggle_notifications',
    'cb_notification_presets',
    'cb_set_notification_preset',
    'cb_set_notif_time',
    'cb_time_hour_range',
    'cb_time_hour',
    'cb_time_set',
    'cb_time_now',
    'cb_time_custom',
    'handle_custom_time_input',
    
    # Keyboards
    'get_notifications_settings_keyboard',
    'get_notification_presets_keyboard',
    'get_time_picker_keyboard',
    'get_minute_picker_keyboard',
    'get_notification_keyboard',
    
    # Utilities
    'format_notification_time',
    'calculate_next_notification_time',
    'get_notification_preset',
    'validate_notification_time',
    'get_time_recommendation',
    'is_time_in_window',
    'clean_user_notification_data',
    'format_notification_summary',
    
    # Constants
    'NOTIFICATION_PRESETS',
    'NOTIFICATION_TYPES',
    'NOTIFICATION_INTERVALS',
    'TIME_PRESETS',
    'NOTIFICATION_MESSAGES',
    'GOAL_COMPLETION_MESSAGES',
    'TIME_CATEGORIES'
]