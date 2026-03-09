"""
Scheduled jobs for notifications
"""

import json
import logging
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes
from sqlalchemy import select

from config import Locale, config
from db import (
    get_pending_notifications, 
    mark_notification_sent, 
    get_user,
    get_session,
    get_today_total
)
from db.models import User
from services import get_user_daily_norm, weather_service
from notifications.constants import NOTIFICATION_MESSAGES, GOAL_COMPLETION_MESSAGES
from common.helpers import get_user_locale

logger = logging.getLogger(__name__)


async def job_minute_check(context: ContextTypes.DEFAULT_TYPE):
    """
    Запускается каждую минуту.
    Проверяет таблицу notification_schedule и отправляет уведомления.
    """
    pending = await get_pending_notifications(limit=200)

    for notif in pending:
        try:
            user = await get_user(notif.user_id)
            if not user or not user.notifications_enabled:
                await mark_notification_sent(notif.id)
                continue

            lang = user.language or "ru"
            
            if notif.notification_type == "smart_reminder":
                await send_smart_reminder(context, user, notif, lang)
            elif notif.notification_type == "morning":
                await send_morning_notification(context, user, notif, lang)
            elif notif.notification_type == "evening":
                await send_evening_notification(context, user, notif, lang)
            else:
                await send_generic_notification(context, user, notif, lang)

            await mark_notification_sent(notif.id)

        except Exception as e:
            logger.error(f"Failed to send notification {notif.id}: {e}")



async def send_smart_reminder(context, user, notif, lang):
    """Send smart reminder notification"""
    ctx = json.loads(notif.context) if notif.context else {}
    glass = ctx.get("glass_number", 1)
    total = ctx.get("total_glasses", 1)
    remaining = ctx.get("remaining_ml", 0)
    glasses_left = (remaining + 249) // 250
    today_total = await get_today_total(user.id)
    
    # ВАЖНО: добавляем await!
    from services import get_user_daily_norm_async
    goal = await get_user_daily_norm_async(user.id)  # Был пропущен await
    
    percent = int((today_total / goal) * 100) if goal > 0 else 0
    
    # Get random message from templates
    from notifications.constants import NOTIFICATION_MESSAGES
    messages = NOTIFICATION_MESSAGES["smart"][lang if lang == "ru" else "en"]
    message = random.choice(messages).format(
        remaining=remaining,
        glasses=glasses_left,
        percent=percent
    )
    
    from water.keyboards import get_notification_keyboard
    keyboard = get_notification_keyboard(lang)
    
    await context.bot.send_message(
        chat_id=user.id,
        text=message,
        reply_markup=keyboard
    )


async def send_morning_notification(context, user, notif, lang):
    """Send morning notification with weather and goal"""
    weather_text = "☀️"
    temperature = None
    
    if user.city:
        weather = await weather_service.get_weather(user.city)
        if weather:
            temperature = weather.temperature
            weather_desc = weather.description
            weather_emoji = weather_service.get_weather_emoji(weather.icon)
            weather_text = f"{weather_emoji} {temperature:.0f}°C, {weather_desc}"
    
    goal = get_user_daily_norm(user.id, temperature or 20)
    
    messages = NOTIFICATION_MESSAGES["morning"][lang if lang == "ru" else "en"]
    message = random.choice(messages).format(
        goal=goal,
        weather=weather_text
    )
    
    from water.keyboards import get_notification_keyboard
    keyboard = get_notification_keyboard(lang)
    
    await context.bot.send_message(
        chat_id=user.id,
        text=message,
        reply_markup=keyboard
    )


async def send_evening_notification(context, user, notif, lang):
    """Send evening summary notification"""
    today_total = await get_today_total(user.id)
    goal = get_user_daily_norm(user.id)
    percent = int((today_total / goal) * 100) if goal > 0 else 0
    
    # Check if goal was completed
    if today_total >= goal:
        completion_messages = GOAL_COMPLETION_MESSAGES[lang if lang == "ru" else "en"]
        message = random.choice(completion_messages)
    else:
        messages = NOTIFICATION_MESSAGES["evening"][lang if lang == "ru" else "en"]
        remaining = goal - today_total
        if remaining > 0:
            motivation = f"Осталось выпить {remaining} мл" if lang == "ru" else f"Remaining: {remaining} ml"
        else:
            motivation = "Отличная работа!" if lang == "ru" else "Great job!"
        
        message = random.choice(messages).format(
            current=today_total,
            goal=goal,
            percent=percent,
            message=motivation
        )
    
    await context.bot.send_message(
        chat_id=user.id,
        text=message
    )


async def send_generic_notification(context, user, notif, lang):
    """Send generic notification"""
    L = Locale.RU if lang == "ru" else Locale.EN
    text = L.get("notif_reminder", "💧 Time to drink!")
    
    from water.keyboards import get_notification_keyboard
    keyboard = get_notification_keyboard(lang)
    
    await context.bot.send_message(
        chat_id=user.id,
        text=text,
        reply_markup=keyboard
    )


async def job_daily_reset(context: ContextTypes.DEFAULT_TYPE):
    """
    Запускается каждый час.
    Проверяет пользователей и перепланирует уведомления.
    """
    reset_hour = config.STREAK_RESET_HOUR  # обычно 6
    
    # ВАЖНО: используем session_manager правильно
    from db.session import session_manager
    
    async with session_manager.session() as session:
        from sqlalchemy import select
        from db.models import User
        
        result = await session.execute(
            select(User).where(User.notifications_enabled == True)
        )
        users = result.scalars().all()
        
        now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))

        for user in users:
            try:
                tz = ZoneInfo(user.timezone or "UTC")
                local_now = now_utc.astimezone(tz)
                if local_now.hour == reset_hour and local_now.minute < 5:
                    from db import reschedule_smart_notifications
                    await reschedule_smart_notifications(user.id)
            except Exception as e:
                logger.error(f"Error in daily reset for user {user.id}: {e}")


def register_jobs(application):
    """Register background jobs"""
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(job_minute_check, interval=60, first=1)
        job_queue.run_repeating(job_daily_reset, interval=3600, first=10)
        logger.info("JobQueue initialized: minute checks and daily reset.")
    else:
        logger.warning("JobQueue not available")