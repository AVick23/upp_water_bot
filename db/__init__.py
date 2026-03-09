"""
Async database module for WaterBot.
"""

from db.engine import init_engine, close_engine, get_engine
from db.session import session_manager, get_db, get_transaction, get_session
from db.models import Base  # Импортируем Base из models
from db.crud import (
    # User
    get_user, create_user, get_or_create_user, update_user,
    complete_registration, update_registration_step, get_registration_data,
    
    # Water logs
    add_water_log, get_today_logs, get_today_total, get_date_total,
    get_logs_for_period, get_drink_breakdown, delete_last_log,
    
    # Achievements
    has_achievement, add_achievement, get_user_achievements,
    get_achievements_count,
    
    # Streak
    update_streak, check_streak_lost,
    
    # Statistics
    get_user_stats, get_week_stats, get_month_heatmap,
    
    # Insights
    add_insight, get_unread_insights, mark_insights_read,
    
    # Notifications
    delete_future_notifications, schedule_notification,
    get_pending_notifications, mark_notification_sent,
    reschedule_smart_notifications,
    
    # Migration
    migrate_legacy_notification_times,
    
    # Favorites
    get_favorite_volumes, add_favorite_volume,
    
    # Export
    export_to_dict, export_to_csv
)


async def init_db():
    """Initialize database engine and session manager"""
    engine = await init_engine()
    session_manager.init()
    
    # СОЗДАЕМ ТАБЛИЦЫ!
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return engine


__all__ = [
    # Engine
    "init_engine",
    "close_engine",
    "get_engine",
    "init_db",
    
    # Session
    "session_manager",
    "get_db",
    "get_transaction",
    "get_session",
    
    # Models base
    "Base",
    
    # All CRUD functions
    "get_user",
    "create_user",
    "get_or_create_user",
    "update_user",
    "complete_registration",
    "update_registration_step",
    "get_registration_data",
    
    "add_water_log",
    "get_today_logs",
    "get_today_total",
    "get_date_total",
    "get_logs_for_period",
    "get_drink_breakdown",
    "delete_last_log",
    
    "has_achievement",
    "add_achievement",
    "get_user_achievements",
    "get_achievements_count",
    
    "update_streak",
    "check_streak_lost",
    
    "get_user_stats",
    "get_week_stats",
    "get_month_heatmap",
    
    "add_insight",
    "get_unread_insights",
    "mark_insights_read",
    
    "delete_future_notifications",
    "schedule_notification",
    "get_pending_notifications",
    "mark_notification_sent",
    "reschedule_smart_notifications",
    
    "migrate_legacy_notification_times",
    
    "get_favorite_volumes",
    "add_favorite_volume",
    
    "export_to_dict",
    "export_to_csv",
]