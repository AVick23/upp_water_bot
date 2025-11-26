# database/db_manager.py
from database.models import DB_PATH
import sqlite3
from typing import Optional, Dict, Any, List
import json
from datetime import datetime, timezone, timedelta
import pytz


class DatabaseManager:
    def __init__(self):
        self._init_db()  # ✅ Добавлено

    def _init_db(self):
        """Инициализация таблиц"""
        from database.models import init_db
        init_db()

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def save_user(self, user_data: Dict[str, Any]) -> None:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (
                user_id, weight, height, gender, activity_level,
                timezone, notification_start, notification_end, city, notifications_enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data["user_id"],
            user_data["weight"],
            user_data["height"],
            user_data["gender"],
            user_data["activity_level"],
            user_data["timezone"],
            user_data["notification_start"],
            user_data["notification_end"],
            user_data.get("city"),
            user_data.get("notifications_enabled", True)
        ))
        conn.commit()
        conn.close()

    def add_water_record(self, user_id: int, ml: int = 250) -> None:
        """Добавляет запись о выпитой воде с учетом часового пояса пользователя"""
        user = self.get_user(user_id)
        if not user:
            return
            
        tz = pytz.timezone(user['timezone'])
        user_today = datetime.now(tz).strftime("%Y-%m-%d")  # ✅ Исправлено
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO water_logs (user_id, date, ml) VALUES (?, ?, ?)",
            (user_id, user_today, ml)
        )
        conn.commit()
        conn.close()

    def get_water_today(self, user_id: int) -> int:
        """Получает количество выпитой воды сегодня (по времени пользователя)"""
        user = self.get_user(user_id)
        if not user:
            return 0
            
        tz = pytz.timezone(user['timezone'])
        user_today = datetime.now(tz).strftime("%Y-%m-%d")  # ✅ Исправлено
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(ml) FROM water_logs WHERE user_id = ? AND date = ?",
            (user_id, user_today)
        )
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0

    def update_notifications_enabled(self, user_id: int, enabled: bool) -> None:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET notifications_enabled = ? WHERE user_id = ?",
            (1 if enabled else 0, user_id)
        )
        conn.commit()
        conn.close()

    def update_user_field(self, user_id: int, field: str, value) -> None:
        allowed_fields = {
            'weight', 'height', 'gender', 'activity_level',
            'timezone', 'notification_start', 'notification_end', 'city'
        }
        if field not in allowed_fields:
            raise ValueError(f"Поле {field} нельзя обновлять")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
        conn.commit()
        conn.close()

    def get_daily_schedule(self, user_id: int, local_date: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM daily_schedule WHERE user_id = ? AND date_local = ?",
            (user_id, local_date)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def save_daily_schedule(self, user_id: int, date_local: str, goal_ml: int, reminder_times: List[str]) -> None:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_schedule (user_id, date_local, generated_at, goal_ml, reminder_times)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            date_local,
            datetime.now(timezone.utc).isoformat(),
            goal_ml,
            json.dumps(reminder_times)
        ))
        conn.commit()
        conn.close()

    def get_all_users_with_notifications_enabled(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE notifications_enabled = 1")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_water_for_period(self, user_id: int, start_date: str, end_date: str) -> int:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(ml) FROM water_logs 
            WHERE user_id = ? AND date BETWEEN ? AND ?
        """, (user_id, start_date, end_date))
        result = cursor.fetchone()[0]
        conn.close()
        return result or 0

    def get_week_dates(self, local_date_str: str, tz_str: str) -> tuple[str, str]:
        tz = pytz.timezone(tz_str)
        dt = tz.localize(datetime.strptime(local_date_str, "%Y-%m-%d"))
        monday = dt - timedelta(days=dt.weekday())
        sunday = monday + timedelta(days=6)
        return monday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d")

    def get_month_dates(self, local_date_str: str) -> tuple[str, str]:
        dt = datetime.strptime(local_date_str, "%Y-%m-%d")
        first = dt.replace(day=1)
        next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
        last = next_month - timedelta(days=1)
        return first.strftime("%Y-%m-%d"), last.strftime("%Y-%m-%d")
    
    def is_reminder_sent_today(self, user_id: int, reminder_type: str) -> bool:
        """Проверяет, было ли уже отправлено уведомление сегодня (по времени пользователя)"""
        user = self.get_user(user_id)
        if not user:
            return False
            
        tz = pytz.timezone(user['timezone'])
        user_today = datetime.now(tz).strftime('%Y-%m-%d')  # ✅ Исправлено
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM sent_reminders WHERE user_id = ? AND date = ? AND reminder_type = ?",
            (user_id, user_today, reminder_type)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def mark_reminder_sent(self, user_id: int, reminder_type: str):
        """Отмечает уведомление как отправленное (по времени пользователя)"""
        user = self.get_user(user_id)
        if not user:
            return
            
        tz = pytz.timezone(user['timezone'])
        user_today = datetime.now(tz).strftime('%Y-%m-%d')  # ✅ Исправлено
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sent_reminders (user_id, date, reminder_type) VALUES (?, ?, ?)",
            (user_id, user_today, reminder_type)
        )
        conn.commit()
        conn.close()