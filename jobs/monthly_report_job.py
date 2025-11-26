# jobs/monthly_report_job.py
from datetime import datetime, timedelta
from telegram.ext import ContextTypes

from database.db_manager import DatabaseManager
from utils.time_utils import get_user_local_time


async def send_monthly_report_for_user(context: ContextTypes.DEFAULT_TYPE, user: dict):
    """
    Отправляет пользователю отчёт о воде за месяц с динамикой.
    """
    db = DatabaseManager()

    # Получаем локальное время пользователя
    local_now = get_user_local_time(user['timezone'])
    current_month_start = local_now.replace(day=1)
    # Последний день текущего месяца
    # Вычисляем первый день следующего месяца, затем вычитаем 1 день
    if local_now.month == 12:
        next_month_first = local_now.replace(year=local_now.year + 1, month=1, day=1)
    else:
        next_month_first = local_now.replace(month=local_now.month + 1, day=1)
    current_month_end = next_month_first - timedelta(days=1)

    current_start = current_month_start.strftime('%Y-%m-%d')
    current_end = current_month_end.strftime('%Y-%m-%d')

    # Текущий месяц
    current_total = db.get_water_for_period(user['user_id'], current_start, current_end)

    # Прошлый месяц
    # Вычисляем первый день прошлого месяца
    if local_now.month == 1:
        # Если сейчас январь, прошлый месяц - декабрь прошлого года
        last_month_first = local_now.replace(year=local_now.year - 1, month=12, day=1)
    else:
        # В остальных случаях просто уменьшаем номер месяца
        last_month_first = local_now.replace(month=local_now.month - 1, day=1)

    # Вычисляем последний день прошлого месяца (первый день текущего - 1 день)
    last_month_end = local_now.replace(day=1) - timedelta(days=1)

    last_start = last_month_first.strftime('%Y-%m-%d')
    last_end = last_month_end.strftime('%Y-%m-%d')

    last_total = db.get_water_for_period(user['user_id'], last_start, last_end)

    # Считаем динамику
    if last_total > 0:
        change_percent = round(((current_total - last_total) / last_total) * 100)
        if change_percent >= 0:
            change_text = f"на {change_percent}% больше"
        else:
            change_text = f"на {abs(change_percent)}% меньше"
    else:
        change_text = "впервые за этот месяц" # или "на 100% больше", если хотите указать рост

    # Отправляем сообщение
    await context.bot.send_message(
        chat_id=user['user_id'],
        text=f"📊 Месячный отчёт:\nС {current_start} по {current_end}\nВыпито: {current_total} мл\n(по сравнению с прошлым месяцем: {change_text})"
    )