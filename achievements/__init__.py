"""
Achievements module for WaterBot
Handles all achievement tracking and display
"""

from telegram.ext import CallbackQueryHandler

from achievements.handlers import (
    cb_achievements,
    cb_achievement_category,
    cb_achievement_detail,
    cb_achievement_rarity,
    cb_achievement_stats,
    cb_achievement_recent,
    cb_achievement_share,
    cb_achievement_share_copy,
    cb_achievement_track,
    cb_achievement_progress_all
)
from achievements.keyboards import (
    get_achievements_main_keyboard,
    get_category_keyboard,
    get_rarity_keyboard,
    get_achievement_detail_keyboard,
    get_achievement_share_keyboard,
    get_achievement_progress_keyboard
)
from achievements.utils import (
    get_user_achievements_data,
    get_achievement_progress,
    get_next_achievements,
    format_achievement_text,
    format_achievement_unlock,
    check_achievement_completion
)
from achievements.constants import (
    ACHIEVEMENT_CATEGORIES,
    RARITY_DISPLAY,
    PROGRESS_THRESHOLDS,
    UNLOCK_MESSAGES,
    STATS_MESSAGES
)
from common.decorators import require_registration


def register_handlers(application):
    """Register all achievements-related handlers"""
    
    # Main achievements menu
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievements),
            pattern="^achievements$"
        )
    )
    
    # Category view
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievement_category),
            pattern="^ach_cat_"
        )
    )
    
    # Achievement detail
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievement_detail),
            pattern="^ach_detail_"
        )
    )
    
    # Rarity view
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievement_rarity),
            pattern="^ach_rarity_"
        )
    )
    
    # Statistics
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievement_stats),
            pattern="^ach_stats$"
        )
    )
    
    # Recent achievements
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievement_recent),
            pattern="^ach_recent$"
        )
    )
    
    # Sharing
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievement_share),
            pattern="^ach_share_[^_]+$"
        )
    )
    
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievement_share_copy),
            pattern="^ach_share_copy_"
        )
    )
    
    # Tracking
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievement_track),
            pattern="^ach_track_"
        )
    )
    
    # Progress
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_achievement_progress_all),
            pattern="^ach_progress_all$"
        )
    )


__all__ = [
    # Registration
    'register_handlers',
    
    # Keyboards
    'get_achievements_main_keyboard',
    'get_category_keyboard',
    'get_rarity_keyboard',
    'get_achievement_detail_keyboard',
    'get_achievement_share_keyboard',
    'get_achievement_progress_keyboard',
    
    # Utilities
    'get_user_achievements_data',
    'get_achievement_progress',
    'get_next_achievements',
    'format_achievement_text',
    'format_achievement_unlock',
    'check_achievement_completion',
    
    # Constants
    'ACHIEVEMENT_CATEGORIES',
    'RARITY_DISPLAY',
    'PROGRESS_THRESHOLDS',
    'UNLOCK_MESSAGES',
    'STATS_MESSAGES'
]