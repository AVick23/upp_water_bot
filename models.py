"""
SQLAlchemy Database Models for WaterBot
Tables: users, water_logs, achievements, notification_schedule
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, DateTime, 
    Date, ForeignKey, Enum as SQLEnum, Text, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from contextlib import contextmanager

from config import Gender, ActivityLevel, ActivityMode, DrinkType, AchievementType, config

Base = declarative_base()


# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    """User profile with settings and preferences"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)  # Telegram user ID
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # Profile data
    weight = Column(Float, nullable=True)  # kg
    height = Column(Float, nullable=True)  # cm
    gender = Column(SQLEnum(Gender), nullable=True)
    activity_level = Column(SQLEnum(ActivityLevel), default=ActivityLevel.MEDIUM)
    
    # Location
    city = Column(String(255), nullable=True)
    timezone = Column(String(50), default="UTC")
    
    # Notification settings
    notification_start = Column(Integer, default=8)   # Hour (0-23)
    notification_end = Column(Integer, default=22)    # Hour (0-23)
    notifications_enabled = Column(Boolean, default=True)
    
    # Activity mode
    activity_mode = Column(SQLEnum(ActivityMode), default=ActivityMode.NORMAL)
    mode_until = Column(Date, nullable=True)  # When to auto-reset mode
    
    # Language
    language = Column(String(5), default="ru")  # "ru" or "en"
    
    # Stats
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_water_ml = Column(Integer, default=0)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    
    # Custom favorite volumes
    favorite_volumes = Column(String(255), nullable=True)  # JSON array as string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_water_at = Column(DateTime, nullable=True)  # Last water intake
    last_active_date = Column(Date, nullable=True)  # For streak calculation
    
    # Registration state
    registration_complete = Column(Boolean, default=False)
    registration_step = Column(String(50), nullable=True)
    registration_data = Column(Text, nullable=True)  # JSON for temp data
    
    # Relationships
    water_logs = relationship("WaterLog", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_users_last_active', 'last_active_date'),
        Index('ix_users_timezone', 'timezone'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


# ============================================================================
# WATER LOG MODEL
# ============================================================================

class WaterLog(Base):
    """Record of water/drink intake"""
    __tablename__ = "water_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Volume data
    volume_ml = Column(Integer, nullable=False)  # Actual volume
    effective_ml = Column(Integer, nullable=False)  # After coefficient
    drink_type = Column(SQLEnum(DrinkType), default=DrinkType.WATER)
    coefficient = Column(Float, default=1.0)
    
    # Timestamp
    logged_at = Column(DateTime, default=datetime.utcnow)
    logged_date = Column(Date, default=date.today)
    
    # Context
    timezone = Column(String(50), default="UTC")
    
    # Relationships
    user = relationship("User", back_populates="water_logs")
    
    # Indexes
    __table_args__ = (
        Index('ix_water_logs_user_date', 'user_id', 'logged_date'),
        Index('ix_water_logs_date', 'logged_date'),
    )
    
    def __repr__(self):
        return f"<WaterLog(id={self.id}, user_id={self.user_id}, volume={self.volume_ml}ml)>"


# ============================================================================
# USER ACHIEVEMENT MODEL
# ============================================================================

class UserAchievement(Base):
    """User's earned achievements"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    achievement_type = Column(SQLEnum(AchievementType), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional context
    context = Column(Text, nullable=True)  # JSON with achievement details
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    
    # Indexes
    __table_args__ = (
        Index('ix_achievements_user_type', 'user_id', 'achievement_type', unique=True),
    )
    
    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, type={self.achievement_type})>"


# ============================================================================
# INSIGHT MODEL
# ============================================================================

class Insight(Base):
    """AI-generated insights about user's water habits"""
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    insight_text = Column(Text, nullable=False)
    insight_type = Column(String(50), nullable=True)  # pattern, recommendation, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="insights")
    
    def __repr__(self):
        return f"<Insight(user_id={self.user_id}, type={self.insight_type})>"


# ============================================================================
# NOTIFICATION SCHEDULE MODEL
# ============================================================================

class NotificationSchedule(Base):
    """Scheduled notifications for users"""
    __tablename__ = "notification_schedule"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    notification_type = Column(String(50), nullable=False)  # morning, reminder, evening
    scheduled_time = Column(DateTime, nullable=False)
    
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('ix_notifications_pending', 'scheduled_time', 'is_sent'),
    )
    
    def __repr__(self):
        return f"<NotificationSchedule(user_id={self.user_id}, type={self.notification_type})>"


# ============================================================================
# DATABASE ENGINE & SESSION
# ============================================================================

engine = None
SessionLocal = None


def init_db(database_url: str = None):
    """Initialize database engine and create tables"""
    global engine, SessionLocal
    
    db_url = database_url or config.DATABASE_URL
    engine = create_engine(db_url, echo=config.DEBUG)
    # expire_on_commit=False - allows accessing attributes after session is closed
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    return engine


def get_session() -> Session:
    """Get database session"""
    global SessionLocal
    if SessionLocal is None:
        init_db()
    return SessionLocal()


@contextmanager
def get_db():
    """Context manager for database sessions"""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ============================================================================
# PYDANTIC SCHEMAS (for internal use)
# ============================================================================

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class UserStats:
    """User statistics for display"""
    today_ml: int = 0
    today_goal: int = 2000
    today_percent: float = 0.0
    streak: int = 0
    week_total: int = 0
    week_average: float = 0.0
    month_total: int = 0
    total_achievements: int = 0
    level: int = 1
    xp: int = 0
    next_level_xp: int = 100


@dataclass 
class DailyLog:
    """Single day water log summary"""
    date: date
    total_ml: int
    goal_ml: int
    percent: float
    logs_count: int
    drink_breakdown: Dict[str, int]  # drink_type -> ml


@dataclass
class WeekStats:
    """Weekly statistics"""
    days: List[DailyLog]
    total_ml: int
    average_ml: float
    best_day: Optional[DailyLog]
    streak: int
