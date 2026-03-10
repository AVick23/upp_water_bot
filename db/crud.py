"""
Async CRUD operations for WaterBot.
"""

import json
import math
import logging
import io
import csv
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from zoneinfo import ZoneInfo

from sqlalchemy import func, and_, select, delete, update
from sqlalchemy.sql import exists

from db.session import session_manager
from db.models import (
    User, WaterLog, UserAchievement, Insight,
    NotificationSchedule
)
from config import (
    Gender, ActivityLevel, ActivityMode, DrinkType, AchievementType,
    DRINK_COEFFICIENTS, WATER_PRESETS, ACHIEVEMENTS, config
)
from services import get_user_daily_norm_async  # Импортируем асинхронную версию

logger = logging.getLogger(__name__)


# ============================================================================
# USER CRUD
# ============================================================================

async def get_user(user_id: int) -> Optional[User]:
    """Get user by Telegram ID."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


async def create_user(
    user_id: int,
    username: str = None,
    first_name: str = None,
    last_name: str = None,
    language: str = "ru"
) -> User:
    """Create a new user."""
    async with session_manager.session() as session:
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            registration_step="weight"
        )
        session.add(user)
        await session.flush()
        return user


async def get_or_create_user(
    user_id: int,
    username: str = None,
    first_name: str = None,
    last_name: str = None,
    language: str = "ru"
) -> User:
    """Get existing user or create new one."""
    user = await get_user(user_id)
    if user:
        # Update basic info if changed
        async with session_manager.session() as session:
            user = await session.get(User, user_id)
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            await session.flush()
            return user
    return await create_user(user_id, username, first_name, last_name, language)


async def update_user(user_id: int, **kwargs) -> Optional[User]:
    """Update user fields."""
    async with session_manager.session() as session:
        user = await session.get(User, user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await session.flush()
        return user


async def complete_registration(user_id: int) -> Optional[User]:
    """Mark user registration as complete."""
    return await update_user(
        user_id,
        registration_complete=True,
        registration_step=None,
        registration_data=None
    )


async def update_registration_step(user_id: int, step: str, data: Dict = None) -> Optional[User]:
    """Update registration step and temp data."""
    return await update_user(
        user_id,
        registration_step=step,
        registration_data=json.dumps(data) if data else None
    )


async def get_registration_data(user_id: int) -> Dict:
    """Get current registration temporary data."""
    user = await get_user(user_id)
    if user and user.registration_data:
        return json.loads(user.registration_data)
    return {}


# ============================================================================
# WATER LOG CRUD
# ============================================================================

async def add_water_log(
    user_id: int,
    volume_ml: int,
    drink_type: DrinkType = DrinkType.WATER,
    timezone: str = "UTC"
) -> WaterLog:
    """Add a water intake record."""
    coefficient = DRINK_COEFFICIENTS.get(drink_type, 1.0)
    effective_ml = int(volume_ml * coefficient)
    
    async with session_manager.session() as session:
        log = WaterLog(
            user_id=user_id,
            volume_ml=volume_ml,
            effective_ml=effective_ml,
            drink_type=drink_type,
            coefficient=coefficient,
            timezone=timezone,
            logged_date=date.today()
        )
        session.add(log)
        
        # Update user stats
        user = await session.get(User, user_id)
        if user:
            user.total_water_ml = (user.total_water_ml or 0) + effective_ml
            user.last_water_at = datetime.utcnow()
            user.last_active_date = date.today()
        
        await session.flush()
        return log


async def get_today_logs(user_id: int) -> List[WaterLog]:
    """Get all water logs for today."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(WaterLog)
            .where(
                and_(
                    WaterLog.user_id == user_id,
                    WaterLog.logged_date == date.today()
                )
            )
        )
        return result.scalars().all()


async def get_today_total(user_id: int) -> int:
    """Get total effective water for today."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(func.sum(WaterLog.effective_ml))
            .where(
                and_(
                    WaterLog.user_id == user_id,
                    WaterLog.logged_date == date.today()
                )
            )
        )
        return result.scalar() or 0


async def get_date_total(user_id: int, target_date: date) -> int:
    """Get total effective water for a specific date."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(func.sum(WaterLog.effective_ml))
            .where(
                and_(
                    WaterLog.user_id == user_id,
                    WaterLog.logged_date == target_date
                )
            )
        )
        return result.scalar() or 0


async def get_logs_for_period(
    user_id: int,
    start_date: date,
    end_date: date
) -> List[WaterLog]:
    """Get all water logs for a date range."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(WaterLog)
            .where(
                and_(
                    WaterLog.user_id == user_id,
                    WaterLog.logged_date >= start_date,
                    WaterLog.logged_date <= end_date
                )
            )
            .order_by(WaterLog.logged_date)
        )
        return result.scalars().all()


async def get_drink_breakdown(user_id: int, target_date: date = None) -> Dict[str, int]:
    """Get breakdown by drink type for a date."""
    target = target_date or date.today()
    async with session_manager.session() as session:
        result = await session.execute(
            select(
                WaterLog.drink_type,
                func.sum(WaterLog.effective_ml)
            )
            .where(
                and_(
                    WaterLog.user_id == user_id,
                    WaterLog.logged_date == target
                )
            )
            .group_by(WaterLog.drink_type)
        )
        return {str(row[0]): row[1] for row in result.all() if row[0]}


async def delete_last_log(user_id: int) -> bool:
    """Delete the most recent water log."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(WaterLog)
            .where(WaterLog.user_id == user_id)
            .order_by(WaterLog.logged_at.desc())
            .limit(1)
        )
        log = result.scalar_one_or_none()
        
        if log:
            # Update user total
            user = await session.get(User, user_id)
            if user:
                user.total_water_ml = max(0, (user.total_water_ml or 0) - log.effective_ml)
            
            await session.delete(log)
            return True
        return False


async def delete_all_logs(user_id: int) -> None:
    """Delete all water logs for a user."""
    async with session_manager.session() as session:
        await session.execute(
            delete(WaterLog).where(WaterLog.user_id == user_id)
        )
        await session.commit()
    logger.info(f"Deleted all logs for user {user_id}")


async def delete_user(user_id: int) -> None:
    """Delete user and all associated data."""
    async with session_manager.session() as session:
        user = await session.get(User, user_id)
        if user:
            await session.delete(user)
            await session.commit()
            logger.info(f"Deleted user {user_id}")


# ============================================================================
# ACHIEVEMENTS CRUD
# ============================================================================

async def has_achievement(user_id: int, achievement_type: AchievementType) -> bool:
    """Check if user has an achievement."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(exists().where(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_type == achievement_type
                )
            ))
        )
        return result.scalar()


async def add_achievement(
    user_id: int,
    achievement_type: AchievementType,
    context: Dict = None
) -> Optional[UserAchievement]:
    """Award an achievement to user."""
    if await has_achievement(user_id, achievement_type):
        return None
    
    async with session_manager.session() as session:
        achievement = UserAchievement(
            user_id=user_id,
            achievement_type=achievement_type,
            context=json.dumps(context) if context else None
        )
        session.add(achievement)
        
        # Add XP to user
        xp = ACHIEVEMENTS.get(achievement_type, {}).get("xp", 0)
        user = await session.get(User, user_id)
        if user:
            user.xp = (user.xp or 0) + xp
            # Level up check (100 XP per level)
            user.level = 1 + (user.xp // 100)
        
        await session.flush()
        return achievement


async def get_user_achievements(user_id: int) -> List[UserAchievement]:
    """Get all user achievements."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.earned_at.desc())
        )
        return result.scalars().all()


async def get_achievements_count(user_id: int) -> int:
    """Get count of user achievements."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(UserAchievement)
            .where(UserAchievement.user_id == user_id)
        )
        return result.scalar() or 0


# ============================================================================
# STREAK MANAGEMENT
# ============================================================================

async def update_streak(user_id: int, reached_goal: bool) -> int:
    """Update user streak based on daily goal achievement."""
    async with session_manager.session() as session:
        user = await session.get(User, user_id)
        if not user:
            return 0
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        if reached_goal:
            if user.last_active_date == yesterday or user.last_active_date == today:
                # Continue streak
                if user.last_active_date != today:
                    user.current_streak = (user.current_streak or 0) + 1
            elif user.last_active_date is None:
                # First day
                user.current_streak = 1
            else:
                # Streak was broken
                user.current_streak = 1
            
            user.longest_streak = max(user.longest_streak or 0, user.current_streak)
            user.last_active_date = today
        
        await session.flush()
        return user.current_streak or 0


async def check_streak_lost(user_id: int) -> bool:
    """Check if user lost their streak (didn't log yesterday)."""
    user = await get_user(user_id)
    if not user or not user.last_active_date:
        return False
    
    yesterday = date.today() - timedelta(days=1)
    return user.last_active_date < yesterday


# ============================================================================
# STATISTICS
# ============================================================================

async def get_user_stats(user_id: int, daily_goal: int = 2000) -> Dict[str, Any]:
    """Get comprehensive user statistics."""
    user = await get_user(user_id)
    if not user:
        return {}
    
    today_ml = await get_today_total(user_id)
    today_percent = round((today_ml / daily_goal) * 100, 1) if daily_goal > 0 else 0
    
    # Week stats
    week_start = date.today() - timedelta(days=7)
    week_logs = await get_logs_for_period(user_id, week_start, date.today())
    week_total = sum(log.effective_ml for log in week_logs)
    week_average = week_total / 7 if week_logs else 0
    
    # Month stats
    month_start = date.today() - timedelta(days=30)
    month_logs = await get_logs_for_period(user_id, month_start, date.today())
    month_total = sum(log.effective_ml for log in month_logs)
    
    return {
        "today_ml": today_ml,
        "today_goal": daily_goal,
        "today_percent": min(today_percent, 100),
        "streak": user.current_streak or 0,
        "week_total": week_total,
        "week_average": round(week_average, 0),
        "month_total": month_total,
        "total_achievements": await get_achievements_count(user_id),
        "level": user.level or 1,
        "xp": user.xp or 0,
        "next_level_xp": 100 - ((user.xp or 0) % 100)
    }


async def get_week_stats(user_id: int, daily_goal: int = 2000) -> Dict[str, Any]:
    """Get detailed weekly statistics."""
    days = []
    best_day = None
    best_ml = 0
    
    for i in range(7):
        target_date = date.today() - timedelta(days=6-i)
        total = await get_date_total(user_id, target_date)
        percent = round((total / daily_goal) * 100, 1) if daily_goal > 0 else 0
        breakdown = await get_drink_breakdown(user_id, target_date)
        
        # Count logs
        async with session_manager.session() as session:
            result = await session.execute(
                select(func.count())
                .select_from(WaterLog)
                .where(
                    and_(
                        WaterLog.user_id == user_id,
                        WaterLog.logged_date == target_date
                    )
                )
            )
            count = result.scalar() or 0
        
        day_data = {
            "date": target_date,
            "total_ml": total,
            "goal_ml": daily_goal,
            "percent": min(percent, 100),
            "logs_count": count,
            "drink_breakdown": breakdown
        }
        days.append(day_data)
        
        if total > best_ml:
            best_ml = total
            best_day = day_data
    
    total_ml = sum(d["total_ml"] for d in days)
    user = await get_user(user_id)
    
    return {
        "days": days,
        "total_ml": total_ml,
        "average_ml": round(total_ml / 7, 0),
        "best_day": best_day,
        "streak": user.current_streak if user else 0
    }


async def get_month_heatmap(user_id: int, daily_goal: int = 2000) -> Dict[date, int]:
    """Get month data for heatmap visualization."""
    result = {}
    month_start = date.today() - timedelta(days=30)
    
    async with session_manager.session() as session:
        rows = await session.execute(
            select(
                WaterLog.logged_date,
                func.sum(WaterLog.effective_ml)
            )
            .where(
                and_(
                    WaterLog.user_id == user_id,
                    WaterLog.logged_date >= month_start
                )
            )
            .group_by(WaterLog.logged_date)
        )
        
        for log_date, total in rows.all():
            percent = int((total / daily_goal) * 100) if daily_goal > 0 else 0
            result[log_date] = min(percent, 150)
    
    return result


# ============================================================================
# INSIGHTS CRUD
# ============================================================================

async def add_insight(user_id: int, text: str, insight_type: str = "general") -> Insight:
    """Add an insight for user."""
    async with session_manager.session() as session:
        insight = Insight(
            user_id=user_id,
            insight_text=text,
            insight_type=insight_type
        )
        session.add(insight)
        await session.flush()
        return insight


async def get_unread_insights(user_id: int) -> List[Insight]:
    """Get unread insights for user."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(Insight)
            .where(
                and_(
                    Insight.user_id == user_id,
                    Insight.is_read == False
                )
            )
            .order_by(Insight.created_at.desc())
        )
        return result.scalars().all()


async def mark_insights_read(user_id: int):
    """Mark all insights as read."""
    async with session_manager.session() as session:
        await session.execute(
            update(Insight)
            .where(
                and_(
                    Insight.user_id == user_id,
                    Insight.is_read == False
                )
            )
            .values(is_read=True)
        )
        await session.commit()


# ============================================================================
# NOTIFICATION SCHEDULE CRUD
# ============================================================================

async def delete_future_notifications(user_id: int):
    """Delete all unsent future notifications."""
    async with session_manager.session() as session:
        await session.execute(
            delete(NotificationSchedule)
            .where(
                and_(
                    NotificationSchedule.user_id == user_id,
                    NotificationSchedule.is_sent == False,
                    NotificationSchedule.scheduled_time > datetime.utcnow()
                )
            )
        )
        await session.commit()


async def schedule_notification(
    user_id: int,
    notification_type: str,
    scheduled_utc: datetime,
    context: dict = None
) -> NotificationSchedule:
    """Create a new scheduled notification."""
    async with session_manager.session() as session:
        notif = NotificationSchedule(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_utc,
            context=json.dumps(context) if context else None
        )
        session.add(notif)
        await session.commit()
        await session.refresh(notif)
        return notif


async def get_pending_notifications(limit: int = 100) -> List[NotificationSchedule]:
    """Get all pending notifications that should be sent now or soon."""
    async with session_manager.session() as session:
        now = datetime.utcnow()
        result = await session.execute(
            select(NotificationSchedule)
            .where(
                and_(
                    NotificationSchedule.is_sent == False,
                    NotificationSchedule.scheduled_time <= now + timedelta(minutes=1)
                )
            )
            .limit(limit)
        )
        return result.scalars().all()


async def mark_notification_sent(notification_id: int):
    """Mark a specific notification as sent."""
    async with session_manager.session() as session:
        await session.execute(
            update(NotificationSchedule)
            .where(NotificationSchedule.id == notification_id)
            .values(is_sent=True, sent_at=datetime.utcnow())
        )
        await session.commit()


# ============================================================================
# SMART NOTIFICATION RESCHEDULING (CORE LOGIC)
# ============================================================================

async def reschedule_smart_notifications(user_id: int):
    """
    Recalculate and recreate all smart reminders for a user
    based on current goal, progress, and notification window.
    """
    user = await get_user(user_id)
    if not user or not user.notifications_enabled:
        await delete_future_notifications(user_id)
        return
    
    # 1. Get local time
    try:
        tz = ZoneInfo(user.timezone or "UTC")
    except Exception:
        tz = ZoneInfo("UTC")
    local_now = datetime.now(tz)
    local_minutes_now = local_now.hour * 60 + local_now.minute
    
    # 2. Notification window boundaries
    start_min = user.notification_start_minutes or 480
    end_min = user.notification_end_minutes or 1320
    
    if local_minutes_now >= end_min:
        await delete_future_notifications(user_id)
        return
    
    effective_start = max(local_minutes_now, start_min)
    
    # 3. Get goal and today's total
    goal = await get_user_daily_norm_async(user_id)
    today_total = await get_today_total(user_id)
    remaining = max(0, goal - today_total)
    
    if remaining <= 0:
        await delete_future_notifications(user_id)
        return
    
    glasses = math.ceil(remaining / 250)
    remaining_minutes = end_min - effective_start
    if remaining_minutes <= 0:
        await delete_future_notifications(user_id)
        return
    
    interval = remaining_minutes / glasses
    
    await delete_future_notifications(user_id)
    
    for i in range(glasses):
        remind_local_minutes = effective_start + (i + 1) * interval
        if remind_local_minutes >= end_min:
            remind_local_minutes = end_min - 1
        
        remind_local_dt = local_now.replace(
            hour=int(remind_local_minutes // 60),
            minute=int(remind_local_minutes % 60),
            second=0, microsecond=0
        )
        if remind_local_dt <= local_now:
            continue
        
        remind_utc = remind_local_dt.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        
        context = {
            "glass_number": i + 1,
            "total_glasses": glasses,
            "remaining_ml": max(0, remaining - (i * 250))
        }
        
        await schedule_notification(user_id, "smart_reminder", remind_utc, context)


# ============================================================================
# MIGRATION: UPDATE LEGACY USERS TO MINUTE-BASED NOTIFICATION TIMES
# ============================================================================

async def migrate_legacy_notification_times():
    """One-time migration: for users with NULL minutes, fill from hours."""
    async with session_manager.session() as session:
        result = await session.execute(
            select(User)
            .where(
                and_(
                    User.notification_start_minutes.is_(None),
                    User.notification_start.isnot(None)
                )
            )
        )
        users = result.scalars().all()
        for user in users:
            user.notification_start_minutes = user.notification_start * 60
            user.notification_end_minutes = user.notification_end * 60
        if users:
            await session.commit()
            logger.info(f"Migrated {len(users)} users to minute-based notification times.")


# ============================================================================
# FAVORITE VOLUMES
# ============================================================================

async def get_favorite_volumes(user_id: int) -> List[int]:
    """Get user's favorite custom volumes."""
    user = await get_user(user_id)
    if not user or not user.favorite_volumes:
        return []
    
    try:
        return json.loads(user.favorite_volumes)
    except:
        return []


async def add_favorite_volume(user_id: int, volume: int) -> List[int]:
    """Add a volume to favorites."""
    async with session_manager.session() as session:
        user = await session.get(User, user_id)
        if not user:
            return []
        
        favorites = await get_favorite_volumes(user_id)
        
        if volume not in favorites and volume not in WATER_PRESETS:
            favorites.append(volume)
            favorites = favorites[-config.MAX_CUSTOM_FAVORITES:]
            user.favorite_volumes = json.dumps(favorites)
        
        await session.flush()
        return favorites


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

async def export_to_dict(user_id: int) -> Dict[str, Any]:
    """Export all user data to dictionary (for JSON export)."""
    user = await get_user(user_id)
    if not user:
        return {}
    
    logs = await get_logs_for_period(
        user_id,
        date.today() - timedelta(days=365),
        date.today()
    )
    achievements = await get_user_achievements(user_id)
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "weight": user.weight,
            "height": user.height,
            "gender": str(user.gender) if user.gender else None,
            "activity_level": str(user.activity_level),
            "city": user.city,
            "timezone": user.timezone,
            "language": user.language,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "total_water_ml": user.total_water_ml,
            "level": user.level,
            "xp": user.xp,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "notification_start_minutes": user.notification_start_minutes,
            "notification_end_minutes": user.notification_end_minutes,
        },
        "water_logs": [
            {
                "date": log.logged_date.isoformat(),
                "volume_ml": log.volume_ml,
                "effective_ml": log.effective_ml,
                "drink_type": str(log.drink_type),
                "logged_at": log.logged_at.isoformat() if log.logged_at else None,
            }
            for log in logs
        ],
        "achievements": [
            {
                "type": str(ach.achievement_type),
                "earned_at": ach.earned_at.isoformat() if ach.earned_at else None,
            }
            for ach in achievements
        ]
    }


async def export_to_csv(user_id: int) -> str:
    """Export water logs to CSV format."""
    logs = await get_logs_for_period(
        user_id,
        date.today() - timedelta(days=365),
        date.today()
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["date", "time", "volume_ml", "effective_ml", "drink_type"])
    
    for log in logs:
        writer.writerow([
            log.logged_date.isoformat(),
            log.logged_at.strftime("%H:%M") if log.logged_at else "",
            log.volume_ml,
            log.effective_ml,
            str(log.drink_type)
        ])
    
    return output.getvalue()