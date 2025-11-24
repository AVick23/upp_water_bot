# handlers/stats_handler.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from services.water_calculator import calculate_norm
from services.weather_service import get_current_temp
from utils.time_utils import get_user_local_time
import pytz
from datetime import datetime, timedelta


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Показываем кнопки выбора периода
    keyboard = [
        [InlineKeyboardButton("📊 Сегодня", callback_data="stats_today")],
        [InlineKeyboardButton("📅 Неделя", callback_data="stats_week")],
        [InlineKeyboardButton("🗓 Месяц", callback_data="stats_month")]
    ]
    await update.message.reply_text("Выберите период:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_stats_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = DatabaseManager()
    user = db.get_user(user_id)

    if not user:
        await query.edit_message_text("Сначала пройдите регистрацию через /start.")
        return

    # Получаем локальное время пользователя
    local_now = get_user_local_time(user['timezone'])
    local_date_str = local_now.strftime('%Y-%m-%d')

    # Определяем даты в зависимости от периода
    period = query.data.split("_")[1]
    if period == "today":
        start_date = local_date_str
        end_date = local_date_str
        period_name = "сегодня"
    elif period == "week":
        # Начало недели (понедельник) в локальном времени
        start_of_week = local_now - timedelta(days=local_now.weekday())
        start_date = start_of_week.strftime('%Y-%m-%d')
        end_date = local_now.strftime('%Y-%m-%d')
        period_name = f"с {start_date} по {end_date}"
    elif period == "month":
        # Начало месяца
        start_of_month = local_now.replace(day=1)
        start_date = start_of_month.strftime('%Y-%m-%d')
        end_date = local_now.strftime('%Y-%m-%d')
        period_name = f"с {start_date} по {end_date}"
    else:
        return

    # Суммируем воду за период
    total_ml = db.get_water_for_period(user_id, start_date, end_date)

    # Считаем норму за день (если за неделю/месяц — умножаем на количество дней)
    # Получаем температуру
    temperature = None
    if user.get("city"):
        temperature = get_current_temp(user["city"])

    daily_norm_ml = calculate_norm(user, temperature=temperature)

    # Количество дней в периоде
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    days_count = (end_dt - start_dt).days + 1

    total_norm_ml = daily_norm_ml * days_count

    # Процент выполнения
    percent = round((total_ml / total_norm_ml) * 100) if total_norm_ml > 0 else 0

    # Формируем сообщение
    message = (
        f"📊 Статистика за {period_name}:\n"
        f"Выпито: {total_ml} мл\n"
        f"Норма: {total_norm_ml} мл ({days_count} дн. × {daily_norm_ml} мл/день)\n"
        f"Выполнено: {percent}%"
    )
    if temperature is not None:
        message += f"\n🌡 Температура: {temperature}°C"

    await query.edit_message_text(message)