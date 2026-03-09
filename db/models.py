"""
SQLAlchemy Database Models for WaterBot
Tables: users, water_logs, achievements, notification_schedule
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    Date, ForeignKey, Enum as SQLEnum, Text, Index
)
from sqlalchemy.orm import relationship, declarative_base

from config import Gender, ActivityLevel, ActivityMode, DrinkType, AchievementType

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)
    activity_level = Column(SQLEnum(ActivityLevel), default=ActivityLevel.MEDIUM)
    
    city = Column(String(255), nullable=True)
    timezone = Column(String(50), default="UTC")
    
    notification_start = Column(Integer, default=8)
    notification_end = Column(Integer, default=22)
    notification_start_minutes = Column(Integer, default=8*60)
    notification_end_minutes = Column(Integer, default=22*60)
    notifications_enabled = Column(Boolean, default=True)
    
    activity_mode = Column(SQLEnum(ActivityMode), default=ActivityMode.NORMAL)
    mode_until = Column(Date, nullable=True)
    
    language = Column(String(5), default="ru")
    
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_water_ml = Column(Integer, default=0)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    
    favorite_volumes = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_water_at = Column(DateTime, nullable=True)
    last_active_date = Column(Date, nullable=True)
    
    registration_complete = Column(Boolean, default=False)
    registration_step = Column(String(50), nullable=True)
    registration_data = Column(Text, nullable=True)
    
    water_logs = relationship("WaterLog", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationSchedule", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_users_last_active', 'last_active_date'),
        Index('ix_users_timezone', 'timezone'),
    )


class WaterLog(Base):
    __tablename__ = "water_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    volume_ml = Column(Integer, nullable=False)
    effective_ml = Column(Integer, nullable=False)
    drink_type = Column(SQLEnum(DrinkType), default=DrinkType.WATER)
    coefficient = Column(Float, default=1.0)
    
    logged_at = Column(DateTime, default=datetime.utcnow)
    logged_date = Column(Date, default=date.today)
    
    timezone = Column(String(50), default="UTC")
    
    user = relationship("User", back_populates="water_logs")
    
    __table_args__ = (
        Index('ix_water_logs_user_date', 'user_id', 'logged_date'),
        Index('ix_water_logs_date', 'logged_date'),
    )


class UserAchievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    achievement_type = Column(SQLEnum(AchievementType), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    context = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="achievements")
    
    __table_args__ = (
        Index('ix_achievements_user_type', 'user_id', 'achievement_type', unique=True),
    )


class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    insight_text = Column(Text, nullable=False)
    insight_type = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="insights")


class NotificationSchedule(Base):
    __tablename__ = "notification_schedule"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    notification_type = Column(String(50), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    context = Column(Text, nullable=True)
    
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")
    
    __table_args__ = (
        Index('ix_notifications_pending', 'scheduled_time', 'is_sent'),
        Index('ix_notifications_user', 'user_id'),
    )