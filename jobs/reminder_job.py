# jobs/reminder_job.py
import json
import logging
from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from services.water_calculator import calculate_norm
from services.weather_service import get_current_temp
from services.scheduler_service import generate_reminder_schedule
from utils.time_utils import get_user_local_time

# Настройка логгера
logger = logging.getLogger(__name__)

async def check_and_send_reminders(context: ContextTypes.DEFAULT_TYPE):
    """
    Сканирующий джоб, запускаемый каждые 5 минут.
    Проверяет, наступил ли день/время для отправки уведомлений или генерации расписания
    для каждого пользователя с включёнными уведомлениями.
    """
    db = DatabaseManager()
    users = db.get_all_users_with_notifications_enabled()

    logger.info(f"Проверка уведомлений для {len(users)} пользователей.")

    for user in users:
        user_id = user['user_id']
        logger.debug(f"Обработка пользователя {user_id} в часовом поясе {user['timezone']}")

        # Получаем ЛОКАЛЬНОЕ время и дату пользователя
        local_now = get_user_local_time(user['timezone'])
        local_date_str = local_now.strftime('%Y-%m-%d')
        
        # Получаем часы и минуты для сравнения
        current_hour = local_now.hour
        current_minute = local_now.minute
        current_time_str = f"{current_hour:02d}:{current_minute:02d}"

        # === 1. Генерация расписания на день ===
        existing_schedule = db.get_daily_schedule(user_id, local_date_str)
        
        if not existing_schedule:
            # Проверяем, наступило ли время начала уведомлений (в пределах 5 минут)
            start_hour, start_minute = map(int, user['notification_start'].split(':'))
            time_diff = (current_hour - start_hour) * 60 + (current_minute - start_minute)
            
            if 0 <= time_diff <= 5:  # В течение 5 минут после notification_start
                logger.info(f"Генерация расписания для пользователя {user_id} на {local_date_str}")
                
                # Получаем погоду и рассчитываем норму
                temp = None
                if user['city']:
                    temp = get_current_temp(user['city'])
                
                norm_ml = calculate_norm(
                    user_data={
                        'weight': user['weight'],
                        'gender': user['gender'],
                        'activity_level': user['activity_level']
                    },
                    temperature=temp
                )
                
                # Округляем до стаканов по 250 мл
                glasses = (norm_ml + 249) // 250  # Округление вверх
                glasses = max(1, glasses)  # Минимум 1 стакан
                
                # Генерируем расписание уведомлений
                reminder_times = generate_reminder_schedule(
                    user['notification_start'],
                    user['notification_end'],
                    glasses
                )
                
                # Сохраняем расписание
                db.save_daily_schedule(user_id, local_date_str, norm_ml, reminder_times)
                existing_schedule = {'reminder_times': json.dumps(reminder_times), 'goal_ml': norm_ml}

        # === 2. Отправка напоминаний ===
        if existing_schedule:
            times = json.loads(existing_schedule['reminder_times'])
            
            for scheduled_time in times:
                scheduled_hour, scheduled_minute = map(int, scheduled_time.split(':'))
                time_diff = (current_hour - scheduled_hour) * 60 + (current_minute - scheduled_minute)
                
                # Проверяем в пределах 5 минут от запланированного времени
                if 0 <= time_diff <= 5:
                    await send_reminder(context, user, existing_schedule, scheduled_time, times)

async def send_reminder(context, user, schedule, scheduled_time, all_times):
    """Отправляет одно напоминание"""
    user_id = user['user_id']
    
    # Определяем тип уведомления
    if scheduled_time == all_times[0]:  # Первое уведомление
        message = await create_morning_message(user, schedule)
    elif scheduled_time == all_times[-1]:  # Последнее уведомление
        message = await create_evening_report(user, schedule)
    else:  # Промежуточные уведомления
        message = "💧 Напоминание: выпейте стакан воды!"
    
    # Создаем клавиатуру
    if scheduled_time != all_times[-1]:  # Для всех кроме последнего - кнопка
        keyboard = [[InlineKeyboardButton("💧 Я выпил (250 мл)", callback_data="drank_water")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
    else:
        reply_markup = None
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=reply_markup
        )
        logger.info(f"Уведомление отправлено пользователю {user_id} в {scheduled_time}")
    except Exception as e:
        logger.error(f"Ошибка отправки пользователю {user_id}: {e}")

async def create_morning_message(user, schedule):
    """Создает утреннее сообщение с погодой и нормой"""
    message = f"☀ Доброе утро!\n"
    message += f"Ваша норма на сегодня: {schedule['goal_ml']} мл\n"
    message += f"Это {schedule['goal_ml'] // 250} стаканов по 250 мл\n"
    
    if user['city']:
        temp = get_current_temp(user['city'])
        if temp is not None:
            message += f"\n🌤 В {user['city']} сейчас {temp}°C"
            if temp > 20:
                message += f"\n💡 Сегодня жарко, не забывайте пить больше воды!"
    
    return message

async def create_evening_report(user, schedule):
    """Создает вечерний отчет"""
    db = DatabaseManager()
    today_water = db.get_water_today(user['user_id'])
    goal_ml = schedule['goal_ml']
    percentage = (today_water / goal_ml) * 100 if goal_ml > 0 else 0
    
    message = f"📊 Итог за день:\n"
    message += f"Выпито: {today_water} мл из {goal_ml} мл\n"
    message += f"Выполнение: {percentage:.1f}%\n"
    
    if percentage >= 100:
        message += "\n🎉 Отличный результат! Вы молодец!"
    elif percentage >= 80:
        message += "\n👍 Хорошо поработали!"
    else:
        message += "\n💪 Завтра будет лучше!"
    
    return message