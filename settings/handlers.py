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
        from db import delete_all_logs
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
        from db import delete_user
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