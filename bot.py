"""
WaterBot - Telegram Bot for Water Tracking
Main bot file with handlers and startup
Using python-telegram-bot v20.7

Usage:
    python bot.py

Environment variables:
    BOT_TOKEN - Telegram Bot Token (required)
    OPENWEATHER_API_KEY - OpenWeatherMap API key (optional)
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, date, timedelta
from typing import Dict, Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

# Import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    config, Locale, get_user_locale, Gender, ActivityLevel, 
    ActivityMode, DrinkType, AchievementType, WATER_PRESETS,
    get_water_keyboard, get_drink_type_keyboard, get_main_keyboard,
    get_settings_keyboard, get_mode_keyboard, get_stats_keyboard,
    get_language_keyboard, get_export_keyboard, get_gender_keyboard,
    get_activity_keyboard, get_back_keyboard
)
from models import init_db
from database import (
    get_or_create_user, get_user, update_user, complete_registration,
    update_registration_step, get_registration_data,
    add_water_log, get_today_total, get_today_logs,
    get_user_stats, get_week_stats, get_month_heatmap,
    get_user_achievements, update_streak,
    init_database, get_favorite_volumes, add_favorite_volume
)
from services import (
    calculate_water_norm, get_user_daily_norm, weather_service,
    achievement_service, insights_service, motivation_service,
    format_main_message, get_user_local_time, export_user_data
)

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO if not config.DEBUG else logging.DEBUG
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONVERSATION STATES
# ============================================================================

(
    STATE_START,
    STATE_WEIGHT,
    STATE_HEIGHT,
    STATE_GENDER,
    STATE_ACTIVITY,
    STATE_TIMEZONE,
    STATE_NOTIFICATION_TIME,
    STATE_CITY,
    STATE_CUSTOM_VOLUME,
) = range(9)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_lang(update: Update) -> str:
    """Get user language from update"""
    user = get_user(update.effective_user.id)
    if user and user.language:
        return user.language
    return get_user_locale(update.effective_user.language_code)


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send main menu to user"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    user = get_user(user_id)
    
    if not user or not user.registration_complete:
        return await start_onboarding(update, context)
    
    # Get stats
    today_ml = get_today_total(user_id)
    
    # Get weather if city is set
    temperature = None
    weather_desc = None
    if user.city:
        weather = await weather_service.get_weather(user.city)
        if weather:
            temperature = weather.temperature
            weather_desc = weather.description
    
    # Calculate daily goal
    goal_ml = get_user_daily_norm(user_id, temperature or 20)
    
    # Format message
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
            message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )


# ============================================================================
# START COMMAND & ONBOARDING
# ============================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    lang = get_user_locale(update.effective_user.language_code)
    
    # Get or create user
    user = get_or_create_user(
        user_id=user_id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name,
        language=lang
    )
    
    if user.registration_complete:
        return await send_main_menu(update, context)
    
    return await start_onboarding(update, context)


async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the onboarding process"""
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    # Send welcome message
    welcome_text = f"{L['welcome_title']}\n\n{L['welcome_text']}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(L["btn_start"], callback_data="start_registration")]
    ])
    
    await update.message.reply_text(
        welcome_text, reply_markup=keyboard
    )
    
    # Wait for "Начать" button click
    return STATE_START


async def onboarding_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle weight input during onboarding - triggered by 'Начать' button"""
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        f"{L['reg_weight']}\n\n_{L['reg_weight_hint']}_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_back_keyboard(lang, "cancel")
    )
    
    return STATE_WEIGHT


async def process_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process weight input"""
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user_id = update.effective_user.id
    
    try:
        weight = float(update.message.text)
        if not 30 <= weight <= 200:
            raise ValueError("Out of range")
        
        update_user(user_id, weight=weight)
        
        # Ask for height
        await update.message.reply_text(
            f"{L['reg_height']}\n\n_{L['reg_height_hint']}_",
            parse_mode=ParseMode.MARKDOWN
        )
        return STATE_HEIGHT
        
    except ValueError:
        await update.message.reply_text(L["error_range_weight"])
        return STATE_WEIGHT


async def process_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process height input"""
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user_id = update.effective_user.id
    
    try:
        height = float(update.message.text)
        if not 100 <= height <= 250:
            raise ValueError("Out of range")
        
        update_user(user_id, height=height)
        
        # Ask for gender
        await update.message.reply_text(
            L["reg_gender"],
            reply_markup=get_gender_keyboard(lang)
        )
        return STATE_GENDER
        
    except ValueError:
        await update.message.reply_text(L["error_range_height"])
        return STATE_HEIGHT


async def process_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process gender selection"""
    lang = get_lang(update)
    user_id = update.effective_user.id
    
    await update.callback_query.answer()
    
    gender_str = update.callback_query.data.split("_")[1]
    gender = Gender(gender_str)
    update_user(user_id, gender=gender)
    
    # Ask for activity level
    L = Locale.RU if lang == "ru" else Locale.EN
    await update.callback_query.edit_message_text(
        L["reg_activity"],
        reply_markup=get_activity_keyboard(lang)
    )
    return STATE_ACTIVITY


async def process_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process activity level selection"""
    lang = get_lang(update)
    user_id = update.effective_user.id
    
    await update.callback_query.answer()
    
    activity_str = update.callback_query.data.split("_")[1]
    activity = ActivityLevel(activity_str)
    update_user(user_id, activity_level=activity)
    
    # Auto-detect timezone
    tz_name = "Europe/Moscow"  # Default for Russian users
    if lang != "ru":
        tz_name = "UTC"
    
    update_user(user_id, timezone=tz_name)
    
    # Ask for city
    L = Locale.RU if lang == "ru" else Locale.EN
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(L["reg_skip"], callback_data="skip_city")]
    ])
    
    await update.callback_query.edit_message_text(
        f"{L['reg_city']}\n\n_{L['reg_city_hint']}_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    return STATE_CITY


async def process_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process city input or skip"""
    lang = get_lang(update)
    user_id = update.effective_user.id
    L = Locale.RU if lang == "ru" else Locale.EN
    
    if update.callback_query:
        await update.callback_query.answer()
        
        if update.callback_query.data == "skip_city":
            # Complete registration
            return await complete_onboarding(update, context)
        
        # Skip button pressed, wait for text input
        return STATE_CITY
    
    # Text input for city
    city = update.message.text.strip()
    update_user(user_id, city=city)
    
    return await complete_onboarding(update, context)


async def complete_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete onboarding and show main menu"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    user = get_user(user_id)
    
    # Calculate initial water norm
    result = calculate_water_norm(
        weight=user.weight,
        gender=user.gender,
        activity_level=user.activity_level
    )
    
    # Complete registration
    complete_registration(user_id)
    
    # Show completion message
    await update.message.reply_text(
        f"{L['reg_complete']}\n\n{L['reg_complete_text'].format(norm=result.final_norm)}"
    )
    
    # Show main menu
    return await send_main_menu(update, context)


async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel onboarding"""
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(L["btn_cancel"])
    
    return ConversationHandler.END


# ============================================================================
# MAIN MENU HANDLERS
# ============================================================================

async def cb_add_water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show water volume selection"""
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        L["add_water_title"],
        reply_markup=get_water_keyboard(lang)
    )


async def cb_water_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle water volume selection - show drink type"""
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    
    data = update.callback_query.data
    
    if data == "water_custom":
        # Ask for custom volume
        await update.callback_query.edit_message_text(
            f"{L['add_water_title']} ({L['add_custom']})",
            reply_markup=get_back_keyboard(lang, "add_water")
        )
        context.user_data["waiting_custom_volume"] = True
        return
    
    if data.startswith("water_"):
        volume = int(data.split("_")[1])
        context.user_data["pending_volume"] = volume
        
        # Show drink type selection
        await update.callback_query.edit_message_text(
            L["add_drink_type"],
            reply_markup=get_drink_type_keyboard(lang)
        )


async def cb_drink_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle drink type selection and log water"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    
    data = update.callback_query.data
    
    if data == "cancel":
        return await send_main_menu(update, context)
    
    if data.startswith("drink_"):
        drink_type_str = data.split("_")[1]
        drink_type = DrinkType(drink_type_str)
        
        volume = context.user_data.get("pending_volume", 250)
        
        # Add water log
        user = get_user(user_id)
        add_water_log(user_id, volume, drink_type, user.timezone if user else "UTC")
        
        # Check achievements
        new_achievements = await achievement_service.check_all_achievements(user_id, volume, drink_type)
        
        # Update streak if goal reached
        today_ml = get_today_total(user_id)
        goal_ml = get_user_daily_norm(user_id)
        
        # Check for level up before
        old_level = user.level if user else 1
        
        if today_ml >= goal_ml:
            update_streak(user_id, True)
        
        # Refresh user after updates
        user = get_user(user_id)
        new_level = user.level if user else 1
        
        # Show success message
        success_text = f"✅ {L['add_success'].format(volume=volume)}"
        
        # Add level up notification
        if new_level > old_level:
            success_text += f"\n\n🎊 {L['notif_level_up'].format(level=new_level)}"
        
        # Add achievement notifications with rarity-based styling
        for ach_type in new_achievements:
            ach_info = achievement_service.get_achievement_info(ach_type, lang)
            rarity = ach_info.get("rarity", "common")
            
            # Format based on rarity
            if rarity == "mythic":
                ach_text = f"\n\n💎✨ {ach_info['name']} ✨💎\n🔴 {ach_info['rarity_name']} • +{ach_info['xp']} XP"
            elif rarity == "legendary":
                ach_text = f"\n\n🌟 {L['notif_achievement_legendary'].format(name=ach_info['name'])} 🌟\n🟡 {ach_info['rarity_name']} • +{ach_info['xp']} XP"
            elif rarity == "epic":
                ach_text = f"\n\n{ach_info['emoji']} **{ach_info['name']}**\n🟣 {ach_info['rarity_name']} • +{ach_info['xp']} XP"
            else:
                ach_text = f"\n\n{ach_info['rarity_emoji']} {ach_info['emoji']} {ach_info['name']}\n+{ach_info['xp']} XP"
            
            success_text += ach_text
        
        await update.callback_query.edit_message_text(success_text)
        
        # Brief pause then show main menu
        await asyncio.sleep(1)
        return await send_main_menu(update, context)


async def handle_custom_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom volume text input"""
    if not context.user_data.get("waiting_custom_volume"):
        return
    
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    try:
        volume = int(update.message.text)
        if volume <= 0 or volume > 5000:
            raise ValueError("Invalid volume")
        
        context.user_data["pending_volume"] = volume
        context.user_data["waiting_custom_volume"] = False
        
        # Offer to save as favorite
        await update.message.reply_text(
            L["add_drink_type"],
            reply_markup=get_drink_type_keyboard(lang)
        )
        
    except ValueError:
        await update.message.reply_text(L["error_invalid_number"])


async def cb_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    await update.callback_query.answer()
    return await send_main_menu(update, context)


# ============================================================================
# STATISTICS HANDLERS
# ============================================================================

async def cb_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics menu"""
    lang = get_lang(update)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "📊 " + ("Статистика" if lang == "ru" else "Statistics"),
        reply_markup=get_stats_keyboard(lang)
    )


async def cb_stats_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics for a period"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    
    period = update.callback_query.data.split("_")[1]
    user = get_user(user_id)
    
    if period == "day":
        today_ml = get_today_total(user_id)
        goal_ml = get_user_daily_norm(user_id)
        percent = round((today_ml / goal_ml) * 100, 1) if goal_ml > 0 else 0
        
        text = (
            f"📅 **{L['main_today']}**\n\n"
            f"💧 {today_ml} / {goal_ml} мл\n"
            f"📊 {min(percent, 100):.0f}%\n"
            f"🔥 {user.current_streak or 0} {L['stats_days']}"
        )
    
    elif period == "week":
        week_stats = get_week_stats(user_id, get_user_daily_norm(user_id))
        
        text = (
            f"📆 **{'Неделя' if lang == 'ru' else 'Week'}**\n\n"
            f"💧 {L['stats_total']}: {week_stats.total_ml} мл\n"
            f"📊 {L['stats_average']}: {week_stats.average_ml:.0f} мл\n"
            f"🔥 {L['stats_streak']}: {week_stats.streak} {L['stats_days']}"
        )
        
        if week_stats.best_day:
            text += f"\n🏆 {L['stats_best_day']}: {week_stats.best_day.total_ml} мл"
    
    elif period == "month":
        heatmap = get_month_heatmap(user_id, get_user_daily_norm(user_id))
        total = sum(heatmap.values())
        
        text = (
            f"🗓️ **{'Месяц' if lang == 'ru' else 'Month'}**\n\n"
            f"💧 {L['stats_total']}: {total} мл\n"
            f"📊 {L['stats_average']}: {total // 30:.0f} мл\n"
            f"🔥 {L['stats_streak']}: {user.current_streak or 0} {L['stats_days']}"
        )
    
    else:  # year
        text = (
            f"📊 **{'Год' if lang == 'ru' else 'Year'}**\n\n"
            f"💧 {L['stats_total']}: {user.total_water_ml or 0} мл\n"
            f"🏆 {L['stats_streak']}: {user.longest_streak or 0} {L['stats_days']}"
        )
    
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_back_keyboard(lang, "stats")
    )


# ============================================================================
# ACHIEVEMENTS HANDLERS
# ============================================================================

async def cb_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show achievements"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    
    achievements = get_user_achievements(user_id)
    
    if not achievements:
        text = "🏆 " + ("Пока нет достижений" if lang == "ru" else "No achievements yet")
    else:
        user = get_user(user_id)
        total_count = len(achievements)
        
        lines = [f"🏆 **{'Достижения' if lang == 'ru' else 'Achievements'}** ({total_count})"]
        lines.append(f"⭐ Level {user.level if user else 1} • {user.xp if user else 0} XP\n")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        
        # Group by rarity for better display
        for ach in achievements[:15]:  # Show last 15
            ach_type = AchievementType(ach.achievement_type)
            info = achievement_service.get_achievement_info(ach_type, lang)
            date_str = ach.earned_at.strftime("%d.%m.%y") if ach.earned_at else ""
            rarity_emoji = info.get("rarity_emoji", "⚪")
            
            lines.append(f"{rarity_emoji} {info['emoji']} {info['name']} • {date_str}")
        
        if total_count > 15:
            lines.append(f"\n_... и ещё {total_count - 15}_")
    
        text = "\n".join(lines)
    
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_back_keyboard(lang)
    )


# ============================================================================
# ABOUT BOT
# ============================================================================

async def cb_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show full bot description and features"""
    lang = get_lang(update)
    
    await update.callback_query.answer()
    
    if lang == "ru":
        text = """💧 **Водный трекер**
_Твой персональный помощник для контроля водного баланса_

━━━━━━━━━━━━━━━━━━━━━━

**🎯 Основные возможности:**

**💧 Учёт воды**
• Быстрое добавление воды (150, 250, 500, 1000 мл)
• Произвольный ввод объёма
• Разные типы напитков: вода, чай, кофе, сок, газировка
• Учёт коэффициентов гидратации

**📊 Индивидуальный расчёт нормы**
• На основе веса, роста, пола
• Учёт уровня активности
• Погодная коррекция (при указании города)
• Формула: вес × 30 мл × коэффициенты

**📈 Статистика**
• Дневной, недельный, месячный, годовой обзор
• Трекинг серий дней (streaks)
• Визуализация прогресса

**🏆 Достижения и геймификация**
• 12 видов достижений
• Серии дней: 7, 30, 100, 365 дней
• Объёмные: 10л, 100л, 1000л
• Особые: Ранняя пташка, Выходной герой
• Система уровней и XP

**🎭 Режимы активности**
• 😊 Обычный — стандартная норма
• 💪 Тренировка — +30% к норме
• 🎯 Фокус — минимум уведомлений
• 🏖️ Отпуск — -20% от нормы

**🔔 Умные уведомления**
• Настраиваемое время напоминаний
• Утреннее приветствие с погодой
• Напоминания о приёме воды

**⚙️ Дополнительно**
• 🌐 Русский/English интерфейс
• 📤 Экспорт данных (CSV/JSON)
• 👤 Редактируемый профиль

━━━━━━━━━━━━━━━━━━━━━━

**📝 Формула расчёта:**
`Базовая норма = вес × 30 × K(пол) × K(активность) × K(погода)`

**Коэффициенты напитков:**
💧 Вода: 100%
🍵 Чай: 90%
☕ Кофе: 80%
🧃 Сок: 70%
🥤 Газировка: 50%

━━━━━━━━━━━━━━━━━━━━━━

**💡 Совет:** Пейте воду регулярно в течение дня, а не залпом. Оптимально — стакан каждый час!

_Версия 1.0 | Создано с ❤️_"""
    else:
        text = """💧 **Water Tracker**
_Your personal hydration assistant_

━━━━━━━━━━━━━━━━━━━━━━

**🎯 Main Features:**

**💧 Water Tracking**
• Quick add presets (150, 250, 500, 1000 ml)
• Custom volume input
• Different drink types: water, tea, coffee, juice, soda
• Hydration coefficients applied

**📊 Personalized Daily Goal**
• Based on weight, height, gender
• Activity level consideration
• Weather adjustment (with city set)
• Formula: weight × 30ml × coefficients

**📈 Statistics**
• Daily, weekly, monthly, yearly overview
• Day streaks tracking
• Progress visualization

**🏆 Achievements & Gamification**
• 12 achievement types
• Streaks: 7, 30, 100, 365 days
• Volume: 10L, 100L, 1000L
• Special: Early Bird, Weekend Hero
• Levels and XP system

**🎭 Activity Modes**
• 😊 Normal — standard goal
• 💪 Workout — +30% to goal
• 🎯 Focus — minimal notifications
• 🏖️ Vacation — -20% from goal

**🔔 Smart Notifications**
• Customizable reminder times
• Morning greeting with weather
• Hydration reminders

**⚙️ Additional Features**
• 🌐 Russian/English interface
• 📤 Data export (CSV/JSON)
• 👤 Editable profile

━━━━━━━━━━━━━━━━━━━━━━

**📝 Calculation Formula:**
`Base goal = weight × 30 × K(gender) × K(activity) × K(weather)`

**Drink Coefficients:**
💧 Water: 100%
🍵 Tea: 90%
☕ Coffee: 80%
🧃 Juice: 70%
🥤 Soda: 50%

━━━━━━━━━━━━━━━━━━━━━━

**💡 Tip:** Drink water regularly throughout the day, not all at once. Ideally — one glass per hour!

_Version 1.0 | Made with ❤️_"""
    
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_back_keyboard(lang)
    )


# ============================================================================
# SETTINGS HANDLERS
# ============================================================================

async def cb_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    lang = get_lang(update)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "⚙️ " + ("Настройки" if lang == "ru" else "Settings"),
        reply_markup=get_settings_keyboard(lang)
    )


async def cb_settings_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show profile info"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user = get_user(user_id)
    
    await update.callback_query.answer()
    
    profile_text = (
        f"👤 **{'Профиль' if lang == 'ru' else 'Profile'}**\n\n"
        f"⚖️ {'Вес' if lang == 'ru' else 'Weight'}: {user.weight or '?'} кг\n"
        f"📏 {'Рост' if lang == 'ru' else 'Height'}: {user.height or '?'} см\n"
        f"👤 {'Пол' if lang == 'ru' else 'Gender'}: {str(user.gender.value) if user.gender else '?'}\n"
        f"🏃 {'Активность' if lang == 'ru' else 'Activity'}: {str(user.activity_level.value) if user.activity_level else '?'}\n"
        f"🏙️ {'Город' if lang == 'ru' else 'City'}: {user.city or '-'}\n"
        f"🌍 {'Часовой пояс' if lang == 'ru' else 'Timezone'}: {user.timezone}\n"
    )
    
    await update.callback_query.edit_message_text(
        profile_text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_back_keyboard(lang, "settings")
    )


async def cb_settings_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show notification settings"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user = get_user(user_id)
    
    await update.callback_query.answer()
    
    status = "✅ " + ("Включены" if lang == "ru" else "Enabled") if user.notifications_enabled else "❌ " + ("Выключены" if lang == "ru" else "Disabled")
    time_range = f"{user.notification_start:02d}:00 - {user.notification_end:02d}:00"
    
    text = (
        f"🔔 **{'Уведомления' if lang == 'ru' else 'Notifications'}**\n\n"
        f"{'Статус' if lang == 'ru' else 'Status'}: {status}\n"
        f"{'Время' if lang == 'ru' else 'Time'}: {time_range}\n"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔔 " + ("Выключить" if user.notifications_enabled else "Включить") if lang == "ru" else "🔔 " + ("Disable" if user.notifications_enabled else "Enable"),
            callback_data="toggle_notifications"
        )],
        [
            InlineKeyboardButton("⏰ " + ("Начало" if lang == "ru" else "Start time"), callback_data="set_notif_start"),
            InlineKeyboardButton("⏰ " + ("Конец" if lang == "ru" else "End time"), callback_data="set_notif_end"),
        ],
        [InlineKeyboardButton(L["btn_back"], callback_data="settings")],
    ])
    
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


async def cb_set_notif_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show time selection for notifications"""
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    
    time_type = update.callback_query.data.split("_")[2]  # start or end
    
    # Generate time buttons (every hour from 6 to 23)
    keyboard_rows = []
    row = []
    for hour in range(6, 24):
        row.append(InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"notif_time_{time_type}_{hour}"))
        if len(row) == 4:
            keyboard_rows.append(row)
            row = []
    if row:
        keyboard_rows.append(row)
    
    keyboard_rows.append([InlineKeyboardButton(L["btn_back"], callback_data="settings_notifications")])
    
    if lang == "ru":
        text = f"⏰ {'Выберите время начала уведомлений' if time_type == 'start' else 'Выберите время окончания уведомлений'}"
    else:
        text = f"⏰ Select {'start time' if time_type == 'start' else 'end time'} for notifications"
    
    await update.callback_query.edit_message_text(
        text, reply_markup=InlineKeyboardMarkup(keyboard_rows)
    )


async def cb_save_notif_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save selected notification time"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    
    await update.callback_query.answer()
    
    # Parse: notif_time_start_8 or notif_time_end_22
    parts = update.callback_query.data.split("_")
    time_type = parts[2]  # start or end
    hour = int(parts[3])
    
    if time_type == "start":
        update_user(user_id, notification_start=hour)
    else:
        update_user(user_id, notification_end=hour)
    
    # Return to notification settings
    return await cb_settings_notifications(update, context)


async def cb_toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle notifications on/off"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    # Toggle
    new_status = not user.notifications_enabled
    update_user(user_id, notifications_enabled=new_status)
    
    # Refresh the menu
    return await cb_settings_notifications(update, context)


async def cb_settings_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show activity mode selection"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    user = get_user(user_id)
    
    await update.callback_query.answer()
    
    current_mode = str(user.activity_mode.value) if user.activity_mode else "normal"
    
    await update.callback_query.edit_message_text(
        "🎭 " + ("Режим активности" if lang == "ru" else "Activity Mode"),
        reply_markup=get_mode_keyboard(lang, current_mode)
    )


async def cb_set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set activity mode"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    
    mode_str = update.callback_query.data.split("_")[1]
    mode = ActivityMode(mode_str)
    
    update_user(user_id, activity_mode=mode)
    
    mode_labels = {
        "normal": L["mode_normal"],
        "workout": L["mode_workout"],
        "focus": L["mode_focus"],
        "vacation": L["mode_vacation"]
    }
    
    await update.callback_query.edit_message_text(
        L["mode_changed"].format(mode=mode_labels.get(mode_str, mode_str))
    )
    
    await asyncio.sleep(1)
    return await send_main_menu(update, context)


async def cb_settings_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection"""
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = str(user.language) if user and user.language else "ru"
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "🌐 Language / Язык",
        reply_markup=get_language_keyboard(lang)
    )


async def cb_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user language"""
    user_id = update.effective_user.id
    
    await update.callback_query.answer()
    
    lang = update.callback_query.data.split("_")[1]
    update_user(user_id, language=lang)
    
    return await send_main_menu(update, context)


async def cb_settings_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show export options"""
    lang = get_lang(update)
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "📤 " + ("Экспорт данных" if lang == "ru" else "Export Data"),
        reply_markup=get_export_keyboard(lang)
    )


async def cb_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export user data"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    
    format_type = update.callback_query.data.split("_")[1]  # csv or json
    
    content, filename = await export_user_data(user_id, format_type)
    
    # Send as document
    from io import BytesIO
    file_bytes = BytesIO(content.encode('utf-8'))
    
    await context.bot.send_document(
        chat_id=user_id,
        document=file_bytes,
        filename=filename,
        caption=L["export_success"]
    )
    
    await update.callback_query.edit_message_text(
        L["export_success"], reply_markup=get_back_keyboard(lang, "settings")
    )


# ============================================================================
# CANCEL HANDLER
# ============================================================================

async def cb_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel button"""
    await update.callback_query.answer()
    return await send_main_menu(update, context)


# ============================================================================
# ERROR HANDLER
# ============================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        lang = "ru"
        if update.effective_user:
            user = get_user(update.effective_user.id)
            if user:
                lang = user.language
        
        L = Locale.RU if lang == "ru" else Locale.EN
        await update.effective_message.reply_text(L["error_unknown"])


# ============================================================================
# SCHEDULED JOBS
# ============================================================================

async def job_morning_notification(context: ContextTypes.DEFAULT_TYPE):
    """Send morning notification to all users"""
    from database import get_session
    from models import User
    
    session = get_session()
    try:
        users = session.query(User).filter(
            User.notifications_enabled == True,
            User.registration_complete == True
        ).all()
        
        for user in users:
            try:
                lang = user.language or "ru"
                L = Locale.RU if lang == "ru" else Locale.EN
                
                # Get weather
                weather_text = ""
                if user.city:
                    weather = await weather_service.get_weather(user.city)
                    if weather:
                        weather_text = f"{weather.temperature:.0f}°C, {weather.description}"
                
                # Calculate norm
                goal_ml = get_user_daily_norm(user.id)
                
                text = L["notif_morning"].format(
                    weather=weather_text or ("нет данных" if lang == "ru" else "N/A"),
                    norm=goal_ml
                )
                
                await context.bot.send_message(user.id, text)
                
            except Exception as e:
                logger.error(f"Failed to send notification to {user.id}: {e}")
    finally:
        session.close()


async def job_reminder_notification(context: ContextTypes.DEFAULT_TYPE):
    """Send reminder notifications"""
    from database import get_session
    from models import User
    
    session = get_session()
    try:
        users = session.query(User).filter(
            User.notifications_enabled == True,
            User.registration_complete == True,
            User.activity_mode != ActivityMode.FOCUS  # Skip focus mode
        ).all()
        
        for user in users:
            try:
                lang = user.language or "ru"
                L = Locale.RU if lang == "ru" else Locale.EN
                
                today_ml = get_today_total(user.id)
                goal_ml = get_user_daily_norm(user.id)
                remaining = max(0, goal_ml - today_ml)
                
                if remaining > 0:
                    text = L["notif_reminder"].format(remaining=remaining)
                    await context.bot.send_message(user.id, text)
                    
            except Exception as e:
                logger.error(f"Failed to send reminder to {user.id}: {e}")
    finally:
        session.close()


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Start the bot"""
    # Initialize database
    init_database()
    
    # Check token
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is required!")
        print("\n❌ Error: BOT_TOKEN is not set!")
        print("Set it with: export BOT_TOKEN='your_token_here'\n")
        return
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Conversation handler for onboarding
    onboarding_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
        ],
        states={
            STATE_START: [
                CallbackQueryHandler(onboarding_weight, pattern="^start_registration$"),
            ],
            STATE_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_weight),
            ],
            STATE_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_height),
            ],
            STATE_GENDER: [
                CallbackQueryHandler(process_gender, pattern="^gender_")
            ],
            STATE_ACTIVITY: [
                CallbackQueryHandler(process_activity, pattern="^activity_")
            ],
            STATE_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_city),
                CallbackQueryHandler(process_city, pattern="^skip_city$")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_onboarding, pattern="^cancel$")
        ],
        per_user=True,
        per_chat=True,
    )
    
    # Add handlers
    application.add_handler(onboarding_handler)
    
    # Main menu handlers
    application.add_handler(CallbackQueryHandler(cb_main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(cb_add_water, pattern="^add_water$"))
    application.add_handler(CallbackQueryHandler(cb_water_volume, pattern="^water_"))
    application.add_handler(CallbackQueryHandler(cb_drink_type, pattern="^drink_"))
    
    # Custom volume handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_volume))
    
    # Statistics handlers
    application.add_handler(CallbackQueryHandler(cb_stats, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(cb_stats_period, pattern="^stats_"))
    
    # Achievements handler
    application.add_handler(CallbackQueryHandler(cb_achievements, pattern="^achievements$"))
    
    # About bot handler
    application.add_handler(CallbackQueryHandler(cb_about, pattern="^about$"))
    
    # Settings handlers
    application.add_handler(CallbackQueryHandler(cb_settings, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(cb_settings_profile, pattern="^settings_profile$"))
    application.add_handler(CallbackQueryHandler(cb_settings_notifications, pattern="^settings_notifications$"))
    application.add_handler(CallbackQueryHandler(cb_toggle_notifications, pattern="^toggle_notifications$"))
    application.add_handler(CallbackQueryHandler(cb_set_notif_time, pattern="^set_notif_"))
    application.add_handler(CallbackQueryHandler(cb_save_notif_time, pattern="^notif_time_"))
    application.add_handler(CallbackQueryHandler(cb_settings_mode, pattern="^settings_mode$"))
    application.add_handler(CallbackQueryHandler(cb_set_mode, pattern="^mode_"))
    application.add_handler(CallbackQueryHandler(cb_settings_language, pattern="^settings_language$"))
    application.add_handler(CallbackQueryHandler(cb_set_language, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(cb_settings_export, pattern="^settings_export$"))
    application.add_handler(CallbackQueryHandler(cb_export_data, pattern="^export_"))
    
    # Cancel handler
    application.add_handler(CallbackQueryHandler(cb_cancel, pattern="^cancel$"))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Schedule jobs (optional - requires APScheduler)
    job_queue = application.job_queue
    if job_queue:
        # Morning notification at 8:00
        job_queue.run_daily(
            job_morning_notification,
            time=datetime.strptime("08:00", "%H:%M").time(),
            days=(0, 1, 2, 3, 4, 5, 6)
        )
        
        # Reminder every 2 hours from 10:00 to 20:00
        for hour in range(10, 21, 2):
            job_queue.run_daily(
                job_reminder_notification,
                time=datetime.strptime(f"{hour}:00", "%H:%M").time(),
                days=(0, 1, 2, 3, 4, 5, 6)
            )
        logger.info("JobQueue initialized - scheduled notifications enabled")
    else:
        logger.warning("JobQueue not available - scheduled notifications disabled. Install APScheduler: pip install APScheduler")
    
    # Start bot
    logger.info("Starting WaterBot...")
    print("\n💧 WaterBot is starting...")
    print("=" * 40)
    print("Bot is ready! Send /start to begin.")
    if not job_queue:
        print("⚠️  Scheduled notifications disabled (APScheduler not installed)")
    print("=" * 40 + "\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()