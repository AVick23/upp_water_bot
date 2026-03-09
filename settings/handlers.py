"""
Handlers for settings module
"""

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from config import Locale, ActivityMode
from db import (
    get_user, update_user, delete_future_notifications,
    reschedule_smart_notifications, export_to_dict, export_to_csv
)
from settings.keyboards import (
    get_settings_main_keyboard,
    get_profile_settings_keyboard,
    get_notifications_settings_keyboard,
    get_notification_presets_keyboard,
    get_time_picker_keyboard,
    get_minute_picker_keyboard,
    get_timezone_keyboard,
    get_mode_keyboard,
    get_language_keyboard,
    get_export_keyboard,
    get_danger_zone_keyboard,
    get_confirmation_keyboard
)
from settings.utils import (
    get_user_settings_display,
    format_settings_summary,
    validate_time_format,
    get_timezone_by_offset,
    get_notification_preset,
    get_language_name
)
from common.decorators import require_registration
from common.helpers import get_user_locale, safe_send_message

logger = logging.getLogger(__name__)


@require_registration
async def cb_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings main menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    # Get user settings for summary
    settings = await get_user_settings_display(user_id)
    summary = format_settings_summary(settings, lang)
    
    await query.edit_message_text(
        summary,
        parse_mode="Markdown",
        reply_markup=get_settings_main_keyboard(lang)
    )


@require_registration
async def cb_settings_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profile settings"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    settings = await get_user_settings_display(user_id)
    
    text = (
        f"👤 **{Locale.get('profile_title', lang)}**\n\n"
        f"⚖️ {Locale.get('profile_weight', lang)}: {settings['weight']} кг\n"
        f"📏 {Locale.get('profile_height', lang)}: {settings['height']} см\n"
        f"{settings['gender_display']}\n"
        f"{settings['activity_display']}\n"
        f"🏙️ {Locale.get('profile_city', lang)}: {settings['city']}\n"
        f"⏰ {Locale.get('notifications', lang)}: {settings['notif_start']} - {settings['notif_end']}"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_profile_settings_keyboard(settings, lang)
    )


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
    
    await query.edit_message_text(
        "🔔 **" + ("Настройки уведомлений", "Notification settings")[lang == "en"] + "**",
        parse_mode="Markdown",
        reply_markup=get_notifications_settings_keyboard(
            enabled=user.notifications_enabled,
            start_minutes=user.notification_start_minutes or 480,
            end_minutes=user.notification_end_minutes or 1320,
            lang=lang
        )
    )


@require_registration
async def cb_toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle notifications on/off"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user = await get_user(user_id)
    
    if not user:
        return
    
    # Toggle
    new_state = not user.notifications_enabled
    await update_user(user_id, notifications_enabled=new_state)
    
    if new_state:
        # Reschedule if turned on
        await reschedule_smart_notifications(user_id)
    else:
        # Delete future notifications if turned off
        await delete_future_notifications(user_id)
    
    # Show updated settings
    await cb_settings_notifications(update, context)


@require_registration
async def cb_notification_presets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show notification presets"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    await query.edit_message_text(
        "🔄 " + ("Выберите пресет уведомлений", "Choose notification preset")[lang == "en"],
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
        
        # Confirm
        await query.edit_message_text(
            "✅ " + ("Пресет применен!", "Preset applied!")[lang == "en"],
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
    context.user_data["notif_time_type"] = time_type
    
    # Get current value
    user = await get_user(user_id)
    current_minutes = (
        user.notification_start_minutes if time_type == "start"
        else user.notification_end_minutes
    ) or (480 if time_type == "start" else 1320)
    
    await query.edit_message_text(
        f"⏰ " + ("Выберите время", "Select time")[lang == "en"],
        reply_markup=get_time_picker_keyboard(time_type, current_minutes, lang)
    )


@require_registration
async def cb_time_hour_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle hour range selection"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    parts = query.data.split("_")
    time_type = parts[3]  # time_hour_range_{type}_{start}_{end}
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
    
    await query.edit_message_text(
        f"⏰ " + ("Выберите час", "Select hour")[lang == "en"],
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
    
    await query.edit_message_text(
        f"⏰ " + ("Выберите минуты", "Select minutes")[lang == "en"],
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
    
    # Confirm and return
    await query.edit_message_text(
        "✅ " + ("Время установлено!", "Time set!")[lang == "en"]
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
    
    # Get current hour
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute
    
    # Update user
    if time_type == "start":
        await update_user(user_id, notification_start_minutes=current_minutes)
    else:
        await update_user(user_id, notification_end_minutes=current_minutes)
    
    # Reschedule
    await reschedule_smart_notifications(user_id)
    
    await query.edit_message_text(
        "✅ " + ("Время установлено!", "Time set!")[lang == "en"]
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
        "hour": hour
    }
    
    await query.edit_message_text(
        f"✏️ " + ("Введите время в формате ЧЧ:ММ", "Enter time in HH:MM format")[lang == "en"]
    )


@require_registration
async def cb_settings_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show timezone settings"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    user = await get_user(user_id)
    current_tz = user.timezone or "UTC"
    
    await query.edit_message_text(
        "🌍 **" + ("Выберите часовой пояс", "Select timezone")[lang == "en"] + "**",
        parse_mode="Markdown",
        reply_markup=get_timezone_keyboard(current_tz, lang)
    )


@require_registration
async def cb_set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set timezone"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    tz_name = query.data.split("_")[2]  # tz_set_{tz}
    
    # Validate timezone
    try:
        ZoneInfo(tz_name)
        await update_user(user_id, timezone=tz_name)
        
        # Reschedule notifications with new timezone
        await reschedule_smart_notifications(user_id)
        
        await query.edit_message_text(
            "✅ " + ("Часовой пояс обновлен!", "Timezone updated!")[lang == "en"]
        )
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Invalid timezone {tz_name}: {e}")
        await query.edit_message_text(
            "❌ " + ("Неверный часовой пояс", "Invalid timezone")[lang == "en"]
        )
        await asyncio.sleep(1)
    
    await cb_settings(update, context)


@require_registration
async def cb_timezone_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-detect timezone"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    # For now, just ask user to select manually
    # In future, could use IP geolocation
    await query.edit_message_text(
        "📍 " + ("Пожалуйста, выберите часовой пояс из списка", "Please select timezone from list")[lang == "en"],
        reply_markup=get_timezone_keyboard("UTC", lang)
    )


@require_registration
async def cb_settings_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show activity mode settings"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    user = await get_user(user_id)
    current_mode = user.activity_mode or ActivityMode.NORMAL
    
    await query.edit_message_text(
        "🎭 **" + ("Режим активности", "Activity mode")[lang == "en"] + "**\n\n"
        "_" + ("Выберите режим, который соответствует вашей текущей активности", 
               "Choose mode that matches your current activity")[lang == "en"] + "_",
        parse_mode="Markdown",
        reply_markup=get_mode_keyboard(current_mode, lang)
    )


@require_registration
async def cb_set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set activity mode"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    mode_str = query.data.split("_")[2]  # mode_set_{mode}
    mode = ActivityMode(mode_str)
    
    await update_user(user_id, activity_mode=mode)
    
    # Reschedule notifications (norm might change)
    await reschedule_smart_notifications(user_id)
    
    await query.edit_message_text(
        "✅ " + ("Режим обновлен!", "Mode updated!")[lang == "en"]
    )
    await asyncio.sleep(1)
    await cb_settings(update, context)


@require_registration
async def cb_settings_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language settings"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    user = await get_user(user_id)
    current_lang = user.language or "ru"
    
    await query.edit_message_text(
        "🌐 **" + ("Выберите язык", "Select language")[lang == "en"] + "**",
        parse_mode="Markdown",
        reply_markup=get_language_keyboard(current_lang, lang)
    )


@require_registration
async def cb_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set language"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    new_lang = query.data.split("_")[2]  # lang_set_{code}
    
    await update_user(user_id, language=new_lang)
    
    # Get updated user for new language
    user = await get_user(user_id)
    lang = user.language or "ru"
    
    await query.edit_message_text(
        "✅ " + ("Язык изменен!", "Language changed!")[lang == "en"]
    )
    await asyncio.sleep(1)
    
    # Return to settings in new language
    await cb_settings(update, context)


@require_registration
async def cb_settings_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show export options"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    await query.edit_message_text(
        "📤 **" + ("Экспорт данных", "Export data")[lang == "en"] + "**\n\n"
        "_" + ("Выберите формат для экспорта ваших данных о воде", 
               "Choose format to export your water data")[lang == "en"] + "_",
        parse_mode="Markdown",
        reply_markup=get_export_keyboard(lang)
    )


@require_registration
async def cb_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export user data"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    format_type = query.data.split("_")[1]  # export_csv or export_json
    
    try:
        if format_type == "csv":
            content = await export_to_csv(user_id)
            filename = f"water_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            data = await export_to_dict(user_id)
            import json
            content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            filename = f"water_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        from io import BytesIO
        file_bytes = BytesIO(content.encode('utf-8'))
        
        await context.bot.send_document(
            chat_id=user_id,
            document=file_bytes,
            filename=filename,
            caption="📤 " + ("Ваши данные", "Your data")[lang == "en"]
        )
        
        await query.edit_message_text(
            "✅ " + ("Экспорт завершен! Файл отправлен.", "Export complete! File sent.")[lang == "en"],
            reply_markup=get_export_keyboard(lang)
        )
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        await query.edit_message_text(
            "❌ " + ("Ошибка при экспорте", "Export error")[lang == "en"],
            reply_markup=get_export_keyboard(lang)
        )


@require_registration
async def cb_settings_danger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show danger zone"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    await query.edit_message_text(
        "⚠️ **" + ("Опасная зона", "Danger zone")[lang == "en"] + "**\n\n"
        "_" + ("Эти действия необратимы! Будьте осторожны.", 
               "These actions cannot be undone! Be careful.")[lang == "en"] + "_",
        parse_mode="Markdown",
        reply_markup=get_danger_zone_keyboard(lang)
    )


@require_registration
async def cb_danger_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle danger zone action"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    action = query.data.split("_")[1]  # danger_reset_stats or danger_delete_account
    
    # Store action in context
    context.user_data["danger_action"] = action
    
    # Get confirmation message
    from settings.constants import DANGER_ACTIONS
    action_info = DANGER_ACTIONS.get(action, {})
    confirm_text = action_info.get(f"confirm_{lang}", "Are you sure?")
    
    await query.edit_message_text(
        f"⚠️ **{confirm_text}**",
        parse_mode="Markdown",
        reply_markup=get_confirmation_keyboard(action, lang)
    )


@require_registration
async def cb_confirm_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm dangerous action"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    action = context.user_data.get("danger_action")
    
    if not action:
        await cb_settings_danger(update, context)
        return
    
    if action == "reset_stats":
        # Reset all water logs but keep user
        from db import delete_all_logs  # You'll need to add this function
        await delete_all_logs(user_id)
        
        await update_user(
            user_id,
            total_water_ml=0,
            current_streak=0,
            xp=0,
            level=1
        )
        
        text = "✅ " + ("Статистика сброшена", "Statistics reset")[lang == "en"]
        
    elif action == "delete_account":
        # Delete user and all associated data
        from db import delete_user  # You'll need to add this function
        await delete_user(user_id)
        
        text = "✅ " + ("Аккаунт удален", "Account deleted")[lang == "en"]
        
        # Send final message and end conversation
        await query.edit_message_text(text)
        return
    
    # Clear stored action
    context.user_data.pop("danger_action", None)
    
    await query.edit_message_text(text)
    await asyncio.sleep(2)
    await cb_settings(update, context)


@require_registration
async def cb_cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel dangerous action"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    # Clear stored action
    context.user_data.pop("danger_action", None)
    
    await query.edit_message_text(
        "✅ " + ("Действие отменено", "Action cancelled")[lang == "en"]
    )
    await asyncio.sleep(1)
    await cb_settings_danger(update, context)


async def handle_custom_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom time input"""
    if "waiting_custom_time" not in context.user_data:
        return
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    time_data = context.user_data["waiting_custom_time"]
    time_type = time_data["type"]
    
    # Validate input
    is_valid, minutes = validate_time_format(update.message.text)
    
    if not is_valid:
        await update.message.reply_text(
            "❌ " + ("Неверный формат. Используйте ЧЧ:ММ", "Invalid format. Use HH:MM")[lang == "en"]
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
    
    await update.message.reply_text(
        "✅ " + ("Время установлено!", "Time set!")[lang == "en"]
    )
    
    # Return to notifications settings
    await cb_settings_notifications(update, context)