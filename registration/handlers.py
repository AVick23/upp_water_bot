"""
Handlers for registration process
"""

import logging
from typing import Dict, Any

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from config import Locale, Gender, ActivityLevel
from db import (
    get_or_create_user, update_user, complete_registration,
    reschedule_smart_notifications, get_user
)
from services import calculate_water_norm, weather_service

from registration.states import (
    STATE_START, STATE_WEIGHT, STATE_HEIGHT, STATE_GENDER,
    STATE_ACTIVITY, STATE_CITY, STATE_EDIT_WEIGHT, STATE_EDIT_HEIGHT,
    STATE_EDIT_CITY
)
from registration.keyboards import (
    get_start_keyboard, get_gender_keyboard, get_activity_keyboard,
    get_city_keyboard, get_cancel_keyboard, get_back_keyboard,
    get_profile_edit_keyboard
)
from registration.utils import (
    validate_weight, validate_height, validate_city,
    get_user_locale, format_registration_complete, extract_user_data
)

logger = logging.getLogger(__name__)


# ============================================================================
# REGISTRATION HANDLERS
# ============================================================================

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command or start registration"""
    user_data = extract_user_data(update)
    lang = get_user_locale(update)
    
    # Get or create user
    user = await get_or_create_user(
        user_id=user_data["user_id"],
        username=user_data["username"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        language=lang
    )
    
    # If registration is complete, go to main menu
    if user and user.registration_complete:
        # Reschedule notifications for returning user
        await reschedule_smart_notifications(user.id)
        return await send_main_menu(update, context)
    
    # Start onboarding
    L = Locale.RU if lang == "ru" else Locale.EN
    welcome_text = f"{L['welcome_title']}\n\n{L['welcome_text']}"
    
    # Initialize registration context
    context.user_data["registration"] = {
        "weight": None,
        "height": None,
        "gender": None,
        "activity": None,
        "city": None
    }
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_start_keyboard(lang)
    )
    return STATE_START


async def onboarding_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask for weight"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await query.edit_message_text(
        f"{L['reg_weight']}\n\n_{L['reg_weight_hint']}_",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard(lang)
    )
    return STATE_WEIGHT


async def process_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process weight input"""
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    is_valid, weight, error_key = validate_weight(update.message.text)
    
    if not is_valid:
        await update.message.reply_text(L[error_key])
        return STATE_WEIGHT
    
    # Save weight
    await update_user(user_id, weight=weight)
    context.user_data["registration"]["weight"] = weight
    
    await update.message.reply_text(
        f"{L['reg_height']}\n\n_{L['reg_height_hint']}_",
        parse_mode="Markdown"
    )
    return STATE_HEIGHT


async def process_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process height input"""
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    is_valid, height, error_key = validate_height(update.message.text)
    
    if not is_valid:
        await update.message.reply_text(L[error_key])
        return STATE_HEIGHT
    
    # Save height
    await update_user(user_id, height=height)
    context.user_data["registration"]["height"] = height
    
    await update.message.reply_text(
        L["reg_gender"],
        reply_markup=get_gender_keyboard(lang)
    )
    return STATE_GENDER


async def process_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process gender selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    gender_str = query.data.split("_")[1]
    gender = Gender(gender_str)
    
    # Save gender
    await update_user(user_id, gender=gender)
    context.user_data["registration"]["gender"] = gender
    
    L = Locale.RU if lang == "ru" else Locale.EN
    await query.edit_message_text(
        L["reg_activity"],
        reply_markup=get_activity_keyboard(lang)
    )
    return STATE_ACTIVITY


async def process_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process activity level selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    activity_str = query.data.split("_")[1]
    activity = ActivityLevel(activity_str)
    
    # Save activity and set default timezone
    await update_user(user_id, activity_level=activity, timezone="UTC")
    context.user_data["registration"]["activity"] = activity
    
    L = Locale.RU if lang == "ru" else Locale.EN
    await query.edit_message_text(
        f"{L['reg_city']}\n\n_{L['reg_city_hint']}_",
        parse_mode="Markdown",
        reply_markup=get_city_keyboard(lang)
    )
    return STATE_CITY


async def process_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process city input or skip"""
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    # Handle skip callback
    if update.callback_query:
        await update.callback_query.answer()
        if update.callback_query.data == "skip_city":
            return await complete_registration_flow(update, context)
        return STATE_CITY
    
    # Handle text input
    is_valid, city, error_key = validate_city(update.message.text)
    
    if not is_valid:
        L = Locale.RU if lang == "ru" else Locale.EN
        await update.message.reply_text(L[error_key])
        return STATE_CITY
    
    # Save city
    await update_user(user_id, city=city)
    context.user_data["registration"]["city"] = city
    
    return await complete_registration_flow(update, context)


async def complete_registration_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Complete registration and show main menu"""
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    # Mark registration as complete
    await complete_registration(user_id)
    
    # Calculate and show norm
    user = await get_user(user_id)
    result = calculate_water_norm(
        weight=user.weight,
        gender=user.gender or Gender.MALE,
        activity_level=user.activity_level or ActivityLevel.MEDIUM
    )
    
    # Schedule notifications
    await reschedule_smart_notifications(user_id)
    
    # Send completion message
    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"{L['reg_complete']}\n\n{L['reg_complete_text'].format(norm=result.final_norm)}"
        )
    else:
        await update.message.reply_text(
            f"{L['reg_complete']}\n\n{L['reg_complete_text'].format(norm=result.final_norm)}"
        )
    
    # Import here to avoid circular imports
    return await send_main_menu(update, context)


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration process"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await query.edit_message_text(L["btn_cancel"])
    return ConversationHandler.END


# ============================================================================
# PROFILE EDITING HANDLERS
# ============================================================================

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile with edit options"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user = await get_user(user_id)
    
    if not user:
        return
    
    # Format notification time
    start_min = user.notification_start_minutes or 480
    end_min = user.notification_end_minutes or 1320
    start_str = f"{start_min//60:02d}:{start_min%60:02d}"
    end_str = f"{end_min//60:02d}:{end_min%60:02d}"
    
    text = (
        f"👤 **{L['profile_title']}**\n\n"
        f"⚖️ {L['profile_weight']}: {user.weight or '?'} кг\n"
        f"📏 {L['profile_height']}: {user.height or '?'} см\n"
        f"👤 {L['profile_gender']}: {str(user.gender.value) if user.gender else '?'}\n"
        f"🏃 {L['profile_activity']}: {str(user.activity_level.value) if user.activity_level else '?'}\n"
        f"🏙️ {L['profile_city']}: {user.city or '-'}\n"
        f"⏰ {L.get('notifications', 'Уведомления')}: {start_str} - {end_str}\n"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_profile_edit_keyboard(lang)
    )


async def edit_field_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start editing a profile field"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    field = query.data.split("_")[1]  # weight, height, city, gender, activity
    context.user_data["editing_field"] = field
    
    if field == "weight":
        await query.edit_message_text(
            L["profile_edit_weight"],
            reply_markup=get_back_keyboard(lang, "settings_profile")
        )
        return STATE_EDIT_WEIGHT
    
    elif field == "height":
        await query.edit_message_text(
            L["profile_edit_height"],
            reply_markup=get_back_keyboard(lang, "settings_profile")
        )
        return STATE_EDIT_HEIGHT
    
    elif field == "city":
        await query.edit_message_text(
            L["profile_edit_city"],
            reply_markup=get_back_keyboard(lang, "settings_profile")
        )
        return STATE_EDIT_CITY
    
    elif field == "gender":
        await query.edit_message_text(
            L["reg_gender"],
            reply_markup=get_gender_keyboard(lang)
        )
        return ConversationHandler.END
    
    elif field == "activity":
        await query.edit_message_text(
            L["reg_activity"],
            reply_markup=get_activity_keyboard(lang)
        )
        return ConversationHandler.END
    
    return ConversationHandler.END


async def edit_weight_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process weight edit"""
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    is_valid, weight, error_key = validate_weight(update.message.text)
    
    if not is_valid:
        await update.message.reply_text(L[error_key])
        return STATE_EDIT_WEIGHT
    
    # Update weight
    await update_user(user_id, weight=weight)
    
    # Reschedule notifications (norm might change)
    await reschedule_smart_notifications(user_id)
    
    await update.message.reply_text(L["profile_updated"])
    
    # Return to profile
    await show_profile(update, context)
    return ConversationHandler.END


async def edit_height_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process height edit"""
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    is_valid, height, error_key = validate_height(update.message.text)
    
    if not is_valid:
        await update.message.reply_text(L[error_key])
        return STATE_EDIT_HEIGHT
    
    # Update height
    await update_user(user_id, height=height)
    
    await update.message.reply_text(L["profile_updated"])
    
    # Return to profile
    await show_profile(update, context)
    return ConversationHandler.END


async def edit_city_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process city edit"""
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    city_text = update.message.text.strip()
    
    if city_text.lower() == "del":
        await update_user(user_id, city=None)
    else:
        is_valid, city, error_key = validate_city(city_text)
        if not is_valid:
            await update.message.reply_text(L[error_key])
            return STATE_EDIT_CITY
        await update_user(user_id, city=city)
    
    # Reschedule notifications (weather might change norm)
    await reschedule_smart_notifications(user_id)
    
    await update.message.reply_text(L["profile_updated"])
    
    # Return to profile
    await show_profile(update, context)
    return ConversationHandler.END


async def update_gender_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update gender or activity from callback"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data.startswith("gender_"):
        gender = Gender(data.split("_")[1])
        await update_user(user_id, gender=gender)
    elif data.startswith("activity_"):
        activity = ActivityLevel(data.split("_")[1])
        await update_user(user_id, activity_level=activity)
    
    # Reschedule notifications (norm changed)
    await reschedule_smart_notifications(user_id)
    
    # Return to profile
    await show_profile(update, context)


# ============================================================================
# CONVERSATION HANDLER CONFIGURATION
# ============================================================================

def get_registration_conversation_handler():
    """Return configured ConversationHandler for registration"""
    
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_registration),
            CallbackQueryHandler(onboarding_weight, pattern="^start_registration$")
        ],
        states={
            STATE_START: [
                CallbackQueryHandler(onboarding_weight, pattern="^start_registration$"),
                CallbackQueryHandler(cancel_registration, pattern="^cancel_registration$")
            ],
            STATE_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_weight),
                CallbackQueryHandler(cancel_registration, pattern="^cancel_registration$")
            ],
            STATE_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_height),
                CallbackQueryHandler(cancel_registration, pattern="^cancel_registration$")
            ],
            STATE_GENDER: [
                CallbackQueryHandler(process_gender, pattern="^gender_"),
                CallbackQueryHandler(cancel_registration, pattern="^cancel_registration$")
            ],
            STATE_ACTIVITY: [
                CallbackQueryHandler(process_activity, pattern="^activity_"),
                CallbackQueryHandler(cancel_registration, pattern="^cancel_registration$")
            ],
            STATE_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_city),
                CallbackQueryHandler(process_city, pattern="^skip_city$"),
                CallbackQueryHandler(cancel_registration, pattern="^cancel_registration$")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_registration, pattern="^cancel_registration$"),
            CommandHandler("cancel", cancel_registration)
        ],
        name="registration_conversation",
        persistent=False,
        per_user=True,
        per_chat=True,
    )


def get_profile_edit_handlers():
    """Return handlers for profile editing (not part of main conversation)"""
    
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_field_start, pattern="^edit_")],
        states={
            STATE_EDIT_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_weight_process),
                CallbackQueryHandler(show_profile, pattern="^settings_profile$")
            ],
            STATE_EDIT_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_height_process),
                CallbackQueryHandler(show_profile, pattern="^settings_profile$")
            ],
            STATE_EDIT_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_city_process),
                CallbackQueryHandler(show_profile, pattern="^settings_profile$")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(show_profile, pattern="^settings_profile$"),
            CommandHandler("cancel", show_profile)
        ],
        name="profile_edit_conversation",
        persistent=False,
        per_user=True,
        per_chat=True,
    )
    

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send main menu to user (defined here to avoid circular imports)"""
    from common.helpers import get_user_locale
    from config import get_main_keyboard
    from db import get_user, get_today_total
    from services import get_user_daily_norm, weather_service, format_main_message
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    user = await get_user(user_id)
    
    if not user or not user.registration_complete:
        return await start_registration(update, context)
    
    today_ml = await get_today_total(user_id)
    temperature = None
    weather_desc = None
    
    if user.city:
        weather = await weather_service.get_weather(user.city)
        if weather:
            temperature = weather.temperature
            weather_desc = weather.description
    
    goal_ml = get_user_daily_norm(user_id, temperature or 20)
    
    message = format_main_message(
        current_ml=today_ml,
        goal_ml=goal_ml,
        streak=user.current_streak or 0,
        temperature=temperature,
        weather_desc=weather_desc,
        lang=lang
    )
    
    keyboard = get_main_keyboard(lang)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message, parse_mode="Markdown", reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            message, parse_mode="Markdown", reply_markup=keyboard
        )