"""
Scheduled jobs for notifications
"""

import json
import logging
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

from telegram.ext import ContextTypes

from config import Locale, config
from db import (
    get_pending_notifications, 
    mark_notification_sent, 
    get_user,
    get_today_total,
    reschedule_smart_notifications
)
from services import get_user_daily_norm_async, weather_service
from notifications.constants import NOTIFICATION_MESSAGES, GOAL_COMPLETION_MESSAGES
from water.keyboards import get_notification_keyboard

logger = logging.getLogger(__name__)


async def job_minute_check(context: ContextTypes.DEFAULT_TYPE):
    """
    Запускается каждую минуту.
    Проверяет таблицу notification_schedule и отправляет уведомления.
    """
    pending = await get_pending_notifications(limit=200)
    
    if pending:
        logger.debug(f"Found {len(pending)} pending notifications")

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
            logger.info(f"Sent {notif.notification_type} notification to user {user.id}")

        except Exception as e:
            logger.error(f"Failed to send notification {notif.id}: {e}")


async def send_smart_reminder(context, user, notif, lang):
    """Send smart reminder notification"""
    ctx = json.loads(notif.context) if notif.context else {}
    glass = ctx.get("glass_number", 1)
    total = ctx.get("total_glasses", 1)
    remaining = ctx.get("remaining_ml", 0)
    glasses_left = (remaining + 249) // 250  # ceil division
    
    today_total = await get_today_total(user.id)
    # ИСПРАВЛЕНО: добавляем await
    goal = await get_user_daily_norm_async(user.id)
    percent = int((today_total / goal) * 100) if goal > 0 else 0
    
    # Get random message from templates
    messages = NOTIFICATION_MESSAGES["smart"][lang if lang == "ru" else "en"]
    message = random.choice(messages).format(
        remaining=remaining,
        glasses=glasses_left,
        percent=percent
    )
    
    keyboard = get_notification_keyboard(lang)
    
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=message,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Failed to send smart reminder to user {user.id}: {e}")


async def send_morning_notification(context, user, notif, lang):
    """Send morning notification with weather and goal"""
    weather_text = "☀️"
    temperature = None
    
    if user.city:
        try:
            weather = await weather_service.get_weather(user.city)
            if weather:
                temperature = weather.temperature
                weather_desc = weather.description
                weather_emoji = weather_service.get_weather_emoji(weather.icon)
                weather_text = f"{weather_emoji} {temperature:.0f}°C, {weather_desc}"
        except Exception as e:
            logger.error(f"Weather fetch failed for user {user.id}: {e}")
    
    # ИСПРАВЛЕНО: добавляем await
    goal = await get_user_daily_norm_async(user.id, temperature or 20)
    
    messages = NOTIFICATION_MESSAGES["morning"][lang if lang == "ru" else "en"]
    message = random.choice(messages).format(
        goal=goal,
        weather=weather_text
    )
    
    keyboard = get_notification_keyboard(lang)
    
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=message,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Failed to send morning notification to user {user.id}: {e}")

async def send_evening_notification(context, user, notif, lang):
    """Send evening summary notification"""
    today_total = await get_today_total(user.id)
    # ИСПРАВЛЕНО: добавляем await
    goal = await get_user_daily_norm_async(user.id)
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
    
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=message
        )
    except Exception as e:
        logger.error(f"Failed to send evening notification to user {user.id}: {e}")


async def send_generic_notification(context, user, notif, lang):
    """Send generic notification"""
    text = "💧 Time to drink water!" if lang == "en" else "💧 Время выпить воды!"
    
    keyboard = get_notification_keyboard(lang)
    
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=text,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Failed to send generic notification to user {user.id}: {e}")


async def job_daily_reset(context: ContextTypes.DEFAULT_TYPE):
    """
    Запускается каждый час.
    Проверяет пользователей и перепланирует уведомления.
    """
    reset_hour = getattr(config, 'STREAK_RESET_HOUR', 6)
    
    from db.session import session_manager
    from db.models import User
    from sqlalchemy import select
    
    now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
    
    try:
        async with session_manager.session() as session:
            result = await session.execute(
                select(User).where(User.notifications_enabled == True)
            )
            users = result.scalars().all()
            
            logger.debug(f"Daily reset check: found {len(users)} users with notifications enabled")
            
            for user in users:
                try:
                    tz = ZoneInfo(user.timezone or "UTC")
                    local_now = now_utc.astimezone(tz)
                    
                    # Check if it's time for daily reset (within 5 min window)
                    if local_now.hour == reset_hour and local_now.minute < 5:
                        logger.info(f"Running daily reset for user {user.id}")
                        await reschedule_smart_notifications(user.id)
                except Exception as e:
                    logger.error(f"Error in daily reset for user {user.id}: {e}")
    except Exception as e:
        logger.error(f"Error in job_daily_reset: {e}")


def register_jobs(application):
    """Register background jobs"""
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(job_minute_check, interval=60, first=1)
        job_queue.run_repeating(job_daily_reset, interval=3600, first=10)
        logger.info("JobQueue initialized: minute checks and daily reset.")
    else:
        logger.warning("JobQueue not available - notifications will not be sent automatically")