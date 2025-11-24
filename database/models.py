# database/models.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/water_bot.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Таблица users (уже есть, но убедимся, что имя колонки правильное)
    # database/models.py (фрагмент)
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
            notifications_enabled BOOLEAN NOT NULL DEFAULT 1,  -- ✅ с "s"!
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )           
    """)
    
    # НОВАЯ ТАБЛИЦА: water_logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,          -- YYYY-MM-DD
            ml INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date_local TEXT NOT NULL,          -- '2025-11-25'
            generated_at TEXT NOT NULL,        -- UTC timestamp
            goal_ml INTEGER NOT NULL,
            reminder_times TEXT NOT NULL       -- JSON: ["08:00", "11:20", ...]
        )
    ''')

    
    conn.commit()
    conn.close()