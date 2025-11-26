# database/models.py
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List

DB_PATH = Path("data/water_bot.db")

# Добавьте эти классы в файл:
class User:
    def __init__(
        self,
        user_id: int,
        weight: int,
        height: int,
        gender: str,
        activity_level: str,
        timezone: str,
        notification_start: str,
        notification_end: str,
        city: Optional[str] = None,
        notifications_enabled: bool = True,
        created_at: Optional[str] = None
    ):
        self.user_id = user_id
        self.weight = weight
        self.height = height
        self.gender = gender
        self.activity_level = activity_level
        self.timezone = timezone
        self.notification_start = notification_start
        self.notification_end = notification_end
        self.city = city
        self.notifications_enabled = notifications_enabled
        self.created_at = created_at or datetime.utcnow().isoformat()

class WaterLog:
    def __init__(self, id: int, user_id: int, date: str, ml: int):
        self.id = id
        self.user_id = user_id
        self.date = date
        self.ml = ml

class DailySchedule:
    def __init__(
        self,
        id: int,
        user_id: int,
        date_local: str,
        generated_at: str,
        goal_ml: int,
        reminder_times: List[str]
    ):
        self.id = id
        self.user_id = user_id
        self.date_local = date_local
        self.generated_at = generated_at
        self.goal_ml = goal_ml
        self.reminder_times = reminder_times

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            weight INTEGER NOT NULL,
            height INTEGER NOT NULL,
            gender TEXT NOT NULL,
            activity_level TEXT NOT NULL,
            timezone TEXT NOT NULL,
            notification_start TEXT NOT NULL,
            notification_end TEXT NOT NULL,
            city TEXT,
            notifications_enabled BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )           
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            ml INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date_local TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            goal_ml INTEGER NOT NULL,
            reminder_times TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            reminder_type TEXT NOT NULL,  -- 'morning', 'reminder_X', 'evening'
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()