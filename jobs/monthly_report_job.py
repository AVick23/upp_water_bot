# jobs/monthly_report_job.py
from datetime import datetime
from telegram.ext import ContextTypes

from database.db_manager import DatabaseManager


async def send_monthly_report(context: ContextTypes.DEFAULT_TYPE):
    # Эта функция вызывается из job_queue, но без user_id — нужно загрузить всех пользователей
    # В MVP мы не будем использовать персональные джобы — отчёты будут в reminder_job
    pass


async def send_monthly_report_for_user(context: ContextTypes.DEFAULT_TYPE, user: dict):
    """
    Отправляет пользователю отчёт о воде за месяц.
    """
    db = DatabaseManager()

    # Получаем даты начала и конца месяца
    local_date_str = datetime.now().strftime('%Y-%m-%d')
    start_date, end_date = db.get_month_dates(local_date_str)

    # Суммируем за месяц
    total_ml = db.get_water_for_period(user['user_id'], start_date, end_date)

    # Отправляем сообщение
    await context.bot.send_message(
        chat_id=user['user_id'],
        text=f"📊 Отчёт за месяц (с {start_date} по {end_date}):\nВыпито: {total_ml} мл."
    )