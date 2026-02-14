"""
Database CRUD Operations for WaterBot
All database interactions are handled here
"""

import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from models import (
    User, WaterLog, UserAchievement, Insight, 
    NotificationSchedule, UserStats, DailyLog, WeekStats,
    get_db, get_session
)
from config import (
    Gender, ActivityLevel, ActivityMode, DrinkType, AchievementType,
    DRINK_COEFFICIENTS, WATER_PRESETS, ACHIEVEMENTS
)


# ============================================================================
# USER CRUD
# ============================================================================

def get_user(user_id: int) -> Optional[User]:
    """Get user by Telegram ID"""
    with get_db() as db:
        return db.query(User).filter(User.id == user_id).first()


def create_user(
    user_id: int, 
    username: str = None, 
    first_name: str = None, 
    last_name: str = None,
    language: str = "ru"
) -> User:
    """Create a new user"""
    with get_db() as db:
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            registration_step="weight"
        )
        db.add(user)
        db.flush()
        return user


def get_or_create_user(
    user_id: int, 
    username: str = None, 
    first_name: str = None, 
    last_name: str = None,
    language: str = "ru"
) -> User:
    """Get existing user or create new one"""
    user = get_user(user_id)
    if user:
        # Update basic info if changed
        with get_db() as db:
            db_user = db.query(User).filter(User.id == user_id).first()
            if username:
                db_user.username = username
            if first_name:
                db_user.first_name = first_name
            if last_name:
                db_user.last_name = last_name
            db.flush()
            return db_user
    return create_user(user_id, username, first_name, last_name, language)


def update_user(user_id: int, **kwargs) -> Optional[User]:
    """Update user fields"""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        db.flush()
        return user


def complete_registration(user_id: int) -> Optional[User]:
    """Mark user registration as complete"""
    return update_user(
        user_id, 
        registration_complete=True, 
        registration_step=None,
        registration_data=None
    )


def update_registration_step(user_id: int, step: str, data: Dict = None) -> Optional[User]:
    """Update registration step and temp data"""
    return update_user(
        user_id,
        registration_step=step,
        registration_data=json.dumps(data) if data else None
    )


def get_registration_data(user_id: int) -> Dict:
    """Get current registration temporary data"""
    user = get_user(user_id)
    if user and user.registration_data:
        return json.loads(user.registration_data)
    return {}


# ============================================================================
# WATER LOG CRUD
# ============================================================================

def add_water_log(
    user_id: int,
    volume_ml: int,
    drink_type: DrinkType = DrinkType.WATER,
    timezone: str = "UTC"
) -> WaterLog:
    """Add a water intake record"""
    coefficient = DRINK_COEFFICIENTS.get(drink_type, 1.0)
    effective_ml = int(volume_ml * coefficient)
    
    with get_db() as db:
        log = WaterLog(
            user_id=user_id,
            volume_ml=volume_ml,
            effective_ml=effective_ml,
            drink_type=drink_type,
            coefficient=coefficient,
            timezone=timezone,
            logged_date=date.today()
        )
        db.add(log)
        
        # Update user stats
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.total_water_ml = (user.total_water_ml or 0) + effective_ml
            user.last_water_at = datetime.utcnow()
            user.last_active_date = date.today()
        
        db.flush()
        return log


def get_today_logs(user_id: int) -> List[WaterLog]:
    """Get all water logs for today"""
    with get_db() as db:
        return db.query(WaterLog).filter(
            and_(
                WaterLog.user_id == user_id,
                WaterLog.logged_date == date.today()
            )
        ).all()


def get_today_total(user_id: int) -> int:
    """Get total effective water for today"""
    with get_db() as db:
        result = db.query(func.sum(WaterLog.effective_ml)).filter(
            and_(
                WaterLog.user_id == user_id,
                WaterLog.logged_date == date.today()
            )
        ).scalar()
        return result or 0


def get_date_total(user_id: int, target_date: date) -> int:
    """Get total effective water for a specific date"""
    with get_db() as db:
        result = db.query(func.sum(WaterLog.effective_ml)).filter(
            and_(
                WaterLog.user_id == user_id,
                WaterLog.logged_date == target_date
            )
        ).scalar()
        return result or 0


def get_logs_for_period(
    user_id: int, 
    start_date: date, 
    end_date: date
) -> List[WaterLog]:
    """Get all water logs for a date range"""
    with get_db() as db:
        return db.query(WaterLog).filter(
            and_(
                WaterLog.user_id == user_id,
                WaterLog.logged_date >= start_date,
                WaterLog.logged_date <= end_date
            )
        ).order_by(WaterLog.logged_date).all()


def get_drink_breakdown(user_id: int, target_date: date = None) -> Dict[str, int]:
    """Get breakdown by drink type for a date"""
    target = target_date or date.today()
    with get_db() as db:
        results = db.query(
            WaterLog.drink_type,
            func.sum(WaterLog.effective_ml)
        ).filter(
            and_(
                WaterLog.user_id == user_id,
                WaterLog.logged_date == target
            )
        ).group_by(WaterLog.drink_type).all()
        
        return {str(r[0]): r[1] for r in results if r[0]}


def delete_last_log(user_id: int) -> bool:
    """Delete the most recent water log"""
    with get_db() as db:
        log = db.query(WaterLog).filter(
            WaterLog.user_id == user_id
        ).order_by(WaterLog.logged_at.desc()).first()
        
        if log:
            # Update user total
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.total_water_ml = max(0, (user.total_water_ml or 0) - log.effective_ml)
            
            db.delete(log)
            return True
        return False


# ============================================================================
# ACHIEVEMENTS CRUD
# ============================================================================

def has_achievement(user_id: int, achievement_type: AchievementType) -> bool:
    """Check if user has an achievement"""
    with get_db() as db:
        return db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_type == achievement_type
            )
        ).first() is not None


def add_achievement(
    user_id: int, 
    achievement_type: AchievementType,
    context: Dict = None
) -> Optional[UserAchievement]:
    """Award an achievement to user"""
    if has_achievement(user_id, achievement_type):
        return None
    
    with get_db() as db:
        achievement = UserAchievement(
            user_id=user_id,
            achievement_type=achievement_type,
            context=json.dumps(context) if context else None
        )
        db.add(achievement)
        
        # Add XP to user
        xp = ACHIEVEMENTS.get(achievement_type, {}).get("xp", 0)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.xp = (user.xp or 0) + xp
            # Level up check (100 XP per level)
            user.level = 1 + (user.xp // 100)
        
        db.flush()
        return achievement


def get_user_achievements(user_id: int) -> List[UserAchievement]:
    """Get all user achievements"""
    with get_db() as db:
        return db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).order_by(UserAchievement.earned_at.desc()).all()


def get_achievements_count(user_id: int) -> int:
    """Get count of user achievements"""
    with get_db() as db:
        return db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).count()


# ============================================================================
# STREAK MANAGEMENT
# ============================================================================

def update_streak(user_id: int, reached_goal: bool) -> int:
    """Update user streak based on daily goal achievement"""
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
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
        
        db.flush()
        return user.current_streak or 0


def check_streak_lost(user_id: int) -> bool:
    """Check if user lost their streak (didn't log yesterday)"""
    user = get_user(user_id)
    if not user or not user.last_active_date:
        return False
    
    yesterday = date.today() - timedelta(days=1)
    return user.last_active_date < yesterday


# ============================================================================
# STATISTICS
# ============================================================================

def get_user_stats(user_id: int, daily_goal: int = 2000) -> UserStats:
    """Get comprehensive user statistics"""
    user = get_user(user_id)
    if not user:
        return UserStats()
    
    today_ml = get_today_total(user_id)
    today_percent = round((today_ml / daily_goal) * 100, 1) if daily_goal > 0 else 0
    
    # Week stats
    week_start = date.today() - timedelta(days=7)
    week_logs = get_logs_for_period(user_id, week_start, date.today())
    week_total = sum(log.effective_ml for log in week_logs)
    week_average = week_total / 7 if week_logs else 0
    
    # Month stats
    month_start = date.today() - timedelta(days=30)
    month_logs = get_logs_for_period(user_id, month_start, date.today())
    month_total = sum(log.effective_ml for log in month_logs)
    
    return UserStats(
        today_ml=today_ml,
        today_goal=daily_goal,
        today_percent=min(today_percent, 100),
        streak=user.current_streak or 0,
        week_total=week_total,
        week_average=round(week_average, 0),
        month_total=month_total,
        total_achievements=get_achievements_count(user_id),
        level=user.level or 1,
        xp=user.xp or 0,
        next_level_xp=100 - ((user.xp or 0) % 100)
    )


def get_week_stats(user_id: int, daily_goal: int = 2000) -> WeekStats:
    """Get detailed weekly statistics"""
    days = []
    best_day = None
    best_ml = 0
    
    for i in range(7):
        target_date = date.today() - timedelta(days=6-i)
        total = get_date_total(user_id, target_date)
        percent = round((total / daily_goal) * 100, 1) if daily_goal > 0 else 0
        breakdown = get_drink_breakdown(user_id, target_date)
        
        # Count logs
        with get_db() as db:
            count = db.query(WaterLog).filter(
                and_(
                    WaterLog.user_id == user_id,
                    WaterLog.logged_date == target_date
                )
            ).count()
        
        daily = DailyLog(
            date=target_date,
            total_ml=total,
            goal_ml=daily_goal,
            percent=min(percent, 100),
            logs_count=count,
            drink_breakdown=breakdown
        )
        days.append(daily)
        
        if total > best_ml:
            best_ml = total
            best_day = daily
    
    total_ml = sum(d.total_ml for d in days)
    user = get_user(user_id)
    
    return WeekStats(
        days=days,
        total_ml=total_ml,
        average_ml=round(total_ml / 7, 0),
        best_day=best_day,
        streak=user.current_streak if user else 0
    )


def get_month_heatmap(user_id: int, daily_goal: int = 2000) -> Dict[date, int]:
    """Get month data for heatmap visualization"""
    result = {}
    month_start = date.today() - timedelta(days=30)
    
    with get_db() as db:
        logs = db.query(
            WaterLog.logged_date,
            func.sum(WaterLog.effective_ml)
        ).filter(
            and_(
                WaterLog.user_id == user_id,
                WaterLog.logged_date >= month_start
            )
        ).group_by(WaterLog.logged_date).all()
        
        for log_date, total in logs:
            percent = int((total / daily_goal) * 100) if daily_goal > 0 else 0
            result[log_date] = min(percent, 150)  # Cap at 150%
    
    return result


# ============================================================================
# INSIGHTS CRUD
# ============================================================================

def add_insight(user_id: int, text: str, insight_type: str = "general") -> Insight:
    """Add an insight for user"""
    with get_db() as db:
        insight = Insight(
            user_id=user_id,
            insight_text=text,
            insight_type=insight_type
        )
        db.add(insight)
        db.flush()
        return insight


def get_unread_insights(user_id: int) -> List[Insight]:
    """Get unread insights for user"""
    with get_db() as db:
        return db.query(Insight).filter(
            and_(
                Insight.user_id == user_id,
                Insight.is_read == False
            )
        ).order_by(Insight.created_at.desc()).all()


def mark_insights_read(user_id: int):
    """Mark all insights as read"""
    with get_db() as db:
        db.query(Insight).filter(
            and_(
                Insight.user_id == user_id,
                Insight.is_read == False
            )
        ).update({"is_read": True})


# ============================================================================
# NOTIFICATION SCHEDULE CRUD
# ============================================================================

def schedule_notification(
    user_id: int,
    notification_type: str,
    scheduled_time: datetime
) -> NotificationSchedule:
    """Schedule a notification"""
    with get_db() as db:
        notif = NotificationSchedule(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time
        )
        db.add(notif)
        db.flush()
        return notif


def get_pending_notifications() -> List[NotificationSchedule]:
    """Get all pending notifications that should be sent now"""
    with get_db() as db:
        return db.query(NotificationSchedule).filter(
            and_(
                NotificationSchedule.is_sent == False,
                NotificationSchedule.scheduled_time <= datetime.utcnow()
            )
        ).all()


def mark_notification_sent(notification_id: int):
    """Mark notification as sent"""
    with get_db() as db:
        db.query(NotificationSchedule).filter(
            NotificationSchedule.id == notification_id
        ).update({
            "is_sent": True,
            "sent_at": datetime.utcnow()
        })


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_to_dict(user_id: int) -> Dict[str, Any]:
    """Export all user data to dictionary (for JSON export)"""
    user = get_user(user_id)
    if not user:
        return {}
    
    logs = get_logs_for_period(
        user_id, 
        date.today() - timedelta(days=365),  # Last year
        date.today()
    )
    achievements = get_user_achievements(user_id)
    
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


def export_to_csv(user_id: int) -> str:
    """Export water logs to CSV format"""
    import io
    import csv
    
    logs = get_logs_for_period(
        user_id,
        date.today() - timedelta(days=365),
        date.today()
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["date", "time", "volume_ml", "effective_ml", "drink_type"])
    
    # Data
    for log in logs:
        writer.writerow([
            log.logged_date.isoformat(),
            log.logged_at.strftime("%H:%M") if log.logged_at else "",
            log.volume_ml,
            log.effective_ml,
            str(log.drink_type)
        ])
    
    return output.getvalue()


# ============================================================================
# FAVORITE VOLUMES
# ============================================================================

def get_favorite_volumes(user_id: int) -> List[int]:
    """Get user's favorite custom volumes"""
    user = get_user(user_id)
    if not user or not user.favorite_volumes:
        return []
    
    try:
        return json.loads(user.favorite_volumes)
    except:
        return []


def add_favorite_volume(user_id: int, volume: int) -> List[int]:
    """Add a volume to favorites"""
    from config import MAX_CUSTOM_FAVORITES
    
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        favorites = get_favorite_volumes(user_id)
        
        if volume not in favorites and volume not in WATER_PRESETS:
            favorites.append(volume)
            # Keep only last N favorites
            favorites = favorites[-MAX_CUSTOM_FAVORITES:]
            user.favorite_volumes = json.dumps(favorites)
        
        db.flush()
        return favorites


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_database():
    """Initialize database on startup"""
    from models import init_db
    init_db()
    print("✅ Database initialized successfully")