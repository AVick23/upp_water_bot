"""
Statistics module for WaterBot
Handles all statistics and data visualization
"""

from telegram.ext import CallbackQueryHandler

from stats.handlers import (
    cb_stats,
    cb_stats_period,
    cb_stats_trends,
    cb_stats_streaks,
    cb_export_data
)
from stats.keyboards import (
    get_stats_keyboard,
    get_detailed_stats_keyboard,
    get_comparison_keyboard,
    get_heatmap_keyboard,
    get_export_keyboard
)
from stats.utils import (
    get_period_data,
    format_heatmap,
    format_time_distribution,
    get_time_distribution,
    get_weekday_distribution,
    format_weekday_distribution,
    compare_periods
)
from stats.constants import (
    PERIODS,
    HEATMAP_LEVELS,
    TIME_SLOTS,
    CHART_SYMBOLS
)
from common.decorators import require_registration


def register_handlers(application):
    """Register all statistics-related handlers"""
    
    # Main stats menu
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_stats),
            pattern="^stats$"
        )
    )
    
    # Period statistics
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_stats_period),
            pattern="^stats_(day|week|month|year|all)"
        )
    )
    
    # Trends and patterns
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_stats_trends),
            pattern="^stats_trends$"
        )
    )
    
    # Streaks
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_stats_streaks),
            pattern="^stats_streaks$"
        )
    )
    
    # Export data
    application.add_handler(
        CallbackQueryHandler(
            require_registration(cb_export_data),
            pattern="^export_(csv|json)"
        )
    )


__all__ = [
    # Registration
    'register_handlers',
    
    # Keyboards
    'get_stats_keyboard',
    'get_detailed_stats_keyboard',
    'get_comparison_keyboard',
    'get_heatmap_keyboard',
    'get_export_keyboard',
    
    # Utilities
    'get_period_data',
    'format_heatmap',
    'format_time_distribution',
    'get_time_distribution',
    'get_weekday_distribution',
    'format_weekday_distribution',
    'compare_periods',
    
    # Constants
    'PERIODS',
    'HEATMAP_LEVELS',
    'TIME_SLOTS',
    'CHART_SYMBOLS'
]