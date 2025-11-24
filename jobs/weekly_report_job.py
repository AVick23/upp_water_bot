# jobs/weekly_report.py
from datetime import datetime, timedelta
from telegram.ext import ContextTypes

from database.db_manager import DatabaseManager
from utils.time_utils import get_user_local_time


async def send_weekly_report(context: ContextTypes.DEFAULT_TYPE):
    # Эта функция вызывается из job_queue, но без user_id — нужно загрузить всех пользователей
    # В MVP мы не будем использовать персональные джобы — отчёты будут в reminder_job
    pass


async def send_weekly_report_for_user(context: ContextTypes.DEFAULT_TYPE, user: dict):
    """
    Отправляет пользователю отчёт о воде за неделю.
    """
    db = DatabaseManager()

    # Получаем даты начала и конца недели в его часовом поясе
    local_date_str = datetime.now().strftime('%Y-%m-%d')
    start_date, end_date = db.get_week_dates(local_date_str, user['timezone'])

    # Суммируем за неделю
    total_ml = db.get_water_for_period(user['user_id'], start_date, end_date)

    # Отправляем сообщение
    await context.bot.send_message(
        chat_id=user['user_id'],
        text=f"📊 Отчёт за неделю (с {start_date} по {end_date}):\nВыпито: {total_ml} мл."
    )