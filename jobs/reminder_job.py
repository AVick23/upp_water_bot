# jobs/reminder_job.py
import json
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database.db_manager import DatabaseManager
from services.water_calculator import calculate_norm
from services.weather_service import get_current_temp  # ← ИСПРАВЛЕНО: было get_current_temperature
from services.scheduler_service import generate_reminder_schedule
from utils.time_utils import get_user_local_time
from jobs.weekly_report_job import send_weekly_report_for_user
from jobs.monthly_report_job import send_monthly_report_for_user


async def check_and_send_reminders(context: ContextTypes.DEFAULT_TYPE):
    db = DatabaseManager()
    users = db.get_all_users_with_notifications_enabled()

    for user in users:
        # Получаем ЛОКАЛЬНОЕ время пользователя
        local_now = get_user_local_time(user['timezone'])
        local_date_str = local_now.strftime('%Y-%m-%d')
        current_weekday = local_now.weekday()  # 0 = понедельник
        current_day = local_now.day
        current_time_str = local_now.strftime('%H:%M')

        # Еженедельный отчёт: понедельник, 09:00
        if current_weekday == 0 and current_time_str == "09:00":
            await send_weekly_report_for_user(context, user)

        # Ежемесячный отчёт: 1-е число, 09:00
        if current_day == 1 and current_time_str == "09:00":
            await send_monthly_report_for_user(context, user)
        

        # === 1. Проверка: нужно ли сгенерировать расписание на сегодня? ===
        existing_schedule = db.get_daily_schedule(user['user_id'], local_date_str)
        if not existing_schedule and current_time_str == user['notification_start']:
            # Получаем погоду
            temp = None
            if user['city']:
                temp = get_current_temp(user['city'])  # ← ИСПРАВЛЕНО: вызов get_current_temp

            # Считаем норму воды
            norm_ml = calculate_norm(
                user_data={
                    'weight': user['weight'],
                    'gender': user['gender'],
                    'activity_level': user['activity_level']
                },
                temperature=temp
            )
            glasses = norm_ml // 250
            if glasses < 1:
                glasses = 1  # минимум 1 стакан

            # Генерируем расписание
            reminder_times = generate_reminder_schedule(
                user['notification_start'],
                user['notification_end'],
                glasses
            )

            # Сохраняем в БД
            db.save_daily_schedule(
                user_id=user['user_id'],
                date_local=local_date_str,
                goal_ml=norm_ml,
                reminder_times=json.dumps(reminder_times)
            )
            existing_schedule = {
                'reminder_times': json.dumps(reminder_times),
                'goal_ml': norm_ml
            }

        # === 2. Отправка напоминаний ===
        if existing_schedule:
            times = json.loads(existing_schedule['reminder_times'])
            if current_time_str in times:
                # Кнопка "Я выпил"
                keyboard = [[InlineKeyboardButton("💧 Я выпил (250 мл)", callback_data="drank_water")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                message = "💧 Напоминание: выпейте стакан воды!"
                if current_time_str == user['notification_start']:
                    message = (
                        f"☀ Доброе утро!\n"
                        f"Ваша норма на сегодня: {existing_schedule['goal_ml']} мл ({len(times)} стаканов)."
                    )
                    if user['city'] and temp is not None:
                        message += f"\nВ {user['city']} сейчас {temp}°C."

                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=message,
                    reply_markup=reply_markup
                )