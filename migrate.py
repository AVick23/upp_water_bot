#!/usr/bin/env python3
"""
Migration script for WaterBot database.
Creates a backup, adds missing columns, migrates legacy data.
"""

import os
import sys
import shutil
from datetime import datetime
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

# Добавляем путь к проекту, чтобы импортировать модули
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from models import Base, User, NotificationSchedule
from database import migrate_legacy_notification_times, get_db

def backup_database(db_url):
    """Create a backup of the database file if it's SQLite."""
    if db_url.startswith('sqlite'):
        # Extract file path from sqlite:///path
        db_path = db_url.replace('sqlite:///', '')
        if os.path.exists(db_path):
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            print(f"✅ Backup created: {backup_path}")
            return backup_path
    else:
        print("⚠️  Automatic backup only supported for SQLite. Please backup manually.")
    return None

def get_missing_columns(engine, table_name, model_columns):
    """Return list of column names that exist in model but not in database table."""
    inspector = inspect(engine)
    existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
    missing = [col for col in model_columns if col not in existing_columns]
    return missing

def add_column(engine, table_name, column_name, column_type):
    """Add a column to the table using raw SQL (adapts to dialect)."""
    with engine.connect() as conn:
        dialect = engine.dialect.name
        if dialect == 'sqlite':
            # SQLite supports limited ALTER TABLE, but ADD COLUMN is fine
            stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        elif dialect == 'postgresql':
            stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        elif dialect == 'mysql':
            stmt = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        else:
            raise NotImplementedError(f"Unsupported dialect: {dialect}")
        
        conn.execute(text(stmt))
        conn.commit()
    print(f"  ➕ Added column {table_name}.{column_name}")

def main():
    print("🔍 Checking database schema...")
    
    db_url = config.DATABASE_URL
    engine = create_engine(db_url, echo=False)
    
    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as e:
        print(f"❌ Cannot connect to database: {e}")
        return
    
    # Backup (only for SQLite)
    backup_database(db_url)
    
    # Define expected columns per table
    expected_columns = {
        'users': [
            'id', 'username', 'first_name', 'last_name', 'weight', 'height',
            'gender', 'activity_level', 'city', 'timezone', 'notification_start',
            'notification_end', 'notification_start_minutes', 'notification_end_minutes',
            'notifications_enabled', 'activity_mode', 'mode_until', 'language',
            'current_streak', 'longest_streak', 'total_water_ml', 'level', 'xp',
            'favorite_volumes', 'created_at', 'updated_at', 'last_water_at',
            'last_active_date', 'registration_complete', 'registration_step',
            'registration_data'
        ],
        'notification_schedule': [
            'id', 'user_id', 'notification_type', 'scheduled_time', 'context',
            'is_sent', 'sent_at', 'created_at'
        ]
    }
    
    # For each table, check and add missing columns
    for table_name, columns in expected_columns.items():
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            print(f"⚠️  Table '{table_name}' does not exist. Creating all tables...")
            Base.metadata.create_all(engine)
            print(f"✅ Table '{table_name}' created.")
            continue
        
        missing = get_missing_columns(engine, table_name, columns)
        if missing:
            print(f"\n📋 Table '{table_name}' is missing columns: {missing}")
            for col in missing:
                # Determine column type from model
                model_class = User if table_name == 'users' else NotificationSchedule
                col_type = model_class.__table__.columns[col].type.compile(engine.dialect)
                add_column(engine, table_name, col, col_type)
        else:
            print(f"✅ Table '{table_name}' has all required columns.")
    
    # Now run the legacy data migration
    print("\n🔄 Running legacy data migration (notification minutes)...")
    migrate_legacy_notification_times()
    print("✅ Migration completed.")
    
    print("\n🎉 Database schema is up to date.")

if __name__ == "__main__":
    main()