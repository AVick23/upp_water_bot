"""
Handlers for notification settings
"""

import asyncio
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import Locale
from db import (
    get_user, update_user, delete_future_notifications,
    reschedule_smart_notifications
)
from notifications.keyboards import (
    get_notifications_settings_keyboard,
    get_notification_presets_keyboard,
    get_time_picker_keyboard,
    get_minute_picker_keyboard
)
from notifications.utils import (
    format_notification_time,
    get_notification_preset,
    validate_notification_time,
    clean_user_notification_data
)
from common.decorators import require_registration
from common.helpers import get_user_locale, safe_send_message, safe_edit_message

logger = logging.getLogger(__name__)


@require_registration
async def cb_settings_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show notification settings"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    user = await get_user(user_id)
    if not user:
        return
    
    # Clean up any stale temp data
    clean_user_notification_data(context, user_id)
    
    # Format current settings
    enabled = user.notifications_enabled
    start_min = user.notification_start_minutes or 480
    end_min = user.notification_end_minutes or 1320
    
    status_text = "✅ Включены" if enabled else "❌ Выключены" if lang == "ru" else "✅ Enabled" if enabled else "❌ Disabled"
    
    text = (
        f"🔔 **{Locale.get('settings_notifications', lang)}**\n\n"
        f"📊 **{'Статус:' if lang == 'ru' else 'Status:'}** {status_text}\n"
        f"⏰ **{'Время:' if lang == 'ru' else 'Time:'}** {format_notification_time(start_min)} - {format_notification_time(end_min)}\n\n"
        f"_{'Настройте время получения уведомлений' if lang == 'ru' else 'Configure when you want to receive notifications'}_"
    )
    
    await safe_edit_message(
        query,
        text,
        parse_mode="Markdown",
        reply_markup=get_notifications_settings_keyboard(enabled, start_min, end_min, lang)
    )


@require_registration
async def cb_toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle notifications on/off"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    user = await get_user(user_id)
    
    if not user:
        return
    
    # Toggle
    new_state = not user.notifications_enabled
    await update_user(user_id, notifications_enabled=new_state)
    
    if new_state:
        # Reschedule if turned on
        await reschedule_smart_notifications(user_id)
        text = "✅ Уведомления включены!" if lang == "ru" else "✅ Notifications enabled!"
    else:
        # Delete future notifications if turned off
        await delete_future_notifications(user_id)
        text = "❌ Уведомления выключены!" if lang == "ru" else "❌ Notifications disabled!"
    
    await query.edit_message_text(text)
    await asyncio.sleep(1)
    await cb_settings_notifications(update, context)


@require_registration
async def cb_notification_presets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show notification presets"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    title = "Выберите пресет уведомлений" if lang == "ru" else "Choose notification preset"
    desc = "Готовые настройки времени для разных режимов дня" if lang == "ru" else "Preset time configurations for different daily routines"
    
    await safe_edit_message(
        query,
        f"🔄 **{title}**\n\n_{desc}_",
        parse_mode="Markdown",
        reply_markup=get_notification_presets_keyboard(lang)
    )


@require_registration
async def cb_set_notification_preset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Apply notification preset"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    preset_id = query.data.split("_")[2]  # notif_preset_{id}
    preset = get_notification_preset(preset_id)
    
    if preset:
        # Update user
        await update_user(
            user_id,
            notification_start_minutes=preset["start"],
            notification_end_minutes=preset["end"]
        )
        
        # Reschedule notifications
        await reschedule_smart_notifications(user_id)
        
        # Clean up temp data
        clean_user_notification_data(context, user_id)
        
        # Confirm
        await safe_edit_message(
            query,
            "✅ " + ("Пресет применен!" if lang == "ru" else "Preset applied!"),
            reply_markup=get_notifications_settings_keyboard(
                enabled=True,
                start_minutes=preset["start"],
                end_minutes=preset["end"],
                lang=lang
            )
        )
    else:
        await cb_notification_presets(update, context)


@require_registration
async def cb_set_notif_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show time picker for notification start/end"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    time_type = query.data.split("_")[2]  # set_notif_start or set_notif_end
    
    # Store in context and clean old data
    clean_user_notification_data(context, user_id)
    context.user_data["notif_time_type"] = time_type
    
    # Get current value
    user = await get_user(user_id)
    current_minutes = (
        user.notification_start_minutes if time_type == "start"
        else user.notification_end_minutes
    ) or (480 if time_type == "start" else 1320)
    
    await safe_edit_message(
        query,
        f"⏰ " + ("Выберите время" if lang == "ru" else "Select time"),
        reply_markup=get_time_picker_keyboard(time_type, current_minutes, lang)
    )


@require_registration
async def cb_time_hour_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle hour range selection"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    parts = query.data.split("_")
    # format: time_hour_range_{type}_{start}_{end}
    time_type = parts[3]
    start_hour = int(parts[4])
    end_hour = int(parts[5])
    
    # Store range in context
    context.user_data["hour_range"] = (start_hour, end_hour)
    
    # Show hour selection within range
    keyboard = []
    row = []
    for hour in range(start_hour, end_hour + 1):
        row.append(InlineKeyboardButton(
            f"{hour:02d}:00",
            callback_data=f"time_hour_{time_type}_{hour}"
        ))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(
        Locale.get("btn_back", lang),
        callback_data=f"set_notif_{time_type}"
    )])
    
    await safe_edit_message(
        query,
        f"⏰ " + ("Выберите час" if lang == "ru" else "Select hour"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@require_registration
async def cb_time_hour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle hour selection"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    parts = query.data.split("_")
    time_type = parts[2]
    hour = int(parts[3])
    
    context.user_data["selected_hour"] = hour
    
    await safe_edit_message(
        query,
        f"⏰ " + ("Выберите минуты" if lang == "ru" else "Select minutes"),
        reply_markup=get_minute_picker_keyboard(time_type, hour, lang)
    )


@require_registration
async def cb_time_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set specific time"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    parts = query.data.split("_")
    time_type = parts[2]
    minutes = int(parts[3])
    
    # Update user
    if time_type == "start":
        await update_user(user_id, notification_start_minutes=minutes)
    else:
        await update_user(user_id, notification_end_minutes=minutes)
    
    # Reschedule notifications
    await reschedule_smart_notifications(user_id)
    
    # Clean up temp data
    clean_user_notification_data(context, user_id)
    
    # Confirm and return
    await query.edit_message_text(
        "✅ " + ("Время установлено!" if lang == "ru" else "Time set!")
    )
    await asyncio.sleep(1)
    await cb_settings_notifications(update, context)


@require_registration
async def cb_time_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set time to current hour"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    parts = query.data.split("_")
    time_type = parts[2]
    
    # Get current time
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    
    # Update user
    if time_type == "start":
        await update_user(user_id, notification_start_minutes=current_minutes)
    else:
        await update_user(user_id, notification_end_minutes=current_minutes)
    
    # Reschedule
    await reschedule_smart_notifications(user_id)
    
    # Clean up temp data
    clean_user_notification_data(context, user_id)
    
    await query.edit_message_text(
        "✅ " + ("Время установлено!" if lang == "ru" else "Time set!")
    )
    await asyncio.sleep(1)
    await cb_settings_notifications(update, context)


@require_registration
async def cb_time_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for custom time input"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    parts = query.data.split("_")
    time_type = parts[2]
    hour = int(parts[3])
    
    context.user_data["waiting_custom_time"] = {
        "type": time_type,
        "hour": hour,
        "message_id": query.message.message_id,
        "chat_id": query.message.chat_id
    }
    
    await safe_edit_message(
        query,
        f"✏️ " + ("Введите время в формате ЧЧ:ММ" if lang == "ru" else "Enter time in HH:MM format")
    )


async def handle_custom_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom time input"""
    if "waiting_custom_time" not in context.user_data:
        return
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    time_data = context.user_data["waiting_custom_time"]
    time_type = time_data["type"]
    
    # Validate input
    is_valid, minutes = validate_notification_time(update.message.text)
    
    if not is_valid or minutes is None:
        await update.message.reply_text(
            "❌ " + ("Неверный формат. Используйте ЧЧ:ММ" if lang == "ru" else "Invalid format. Use HH:MM")
        )
        return
    
    # Update user
    if time_type == "start":
        await update_user(user_id, notification_start_minutes=minutes)
    else:
        await update_user(user_id, notification_end_minutes=minutes)
    
    # Reschedule
    await reschedule_smart_notifications(user_id)
    
    # Clear waiting state
    context.user_data.pop("waiting_custom_time", None)
    clean_user_notification_data(context, user_id)
    
    await update.message.reply_text(
        "✅ " + ("Время установлено!" if lang == "ru" else "Time set!")
    )
    
    # Создаем искусственный callback_query для возврата в настройки
    # Это более безопасный подход, чем MockCallbackQuery
    from telegram import CallbackQuery
    from types import SimpleNamespace
    
    # Создаем объект, похожий на CallbackQuery
    fake_query = SimpleNamespace()
    fake_query.message = update.message
    fake_query.from_user = update.effective_user
    
    async def fake_answer():
        pass
    
    fake_query.answer = fake_answer
    
    # Временно подменяем callback_query в update
    original_callback_query = update.callback_query
    update.callback_query = fake_query
    
    try:
        # Возвращаемся в настройки уведомлений
        await cb_settings_notifications(update, context)
    finally:
        # Восстанавливаем оригинальный callback_query
        update.callback_query = original_callback_query