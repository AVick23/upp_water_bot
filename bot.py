"""
WaterBot - Telegram Bot for Water Tracking
Main bot file with handlers and startup
Using python-telegram-bot v20.7
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    config, Locale, get_user_locale, Gender, ActivityLevel, 
    ActivityMode, DrinkType, AchievementType, WATER_PRESETS, DRINK_COEFFICIENTS,
    get_water_keyboard, get_drink_category_keyboard, get_drink_type_keyboard, 
    get_main_keyboard, get_settings_keyboard, get_profile_keyboard, get_mode_keyboard, 
    get_stats_keyboard, get_language_keyboard, get_export_keyboard, get_gender_keyboard,
    get_activity_keyboard, get_back_keyboard, get_timezone_keyboard
)
from models import init_db
from database import (
    get_or_create_user, get_user, update_user, complete_registration,
    add_water_log, get_today_total, get_user_stats, get_week_stats, 
    get_month_heatmap, get_user_achievements, update_streak, init_database
)
from services import (
    calculate_water_norm, get_user_daily_norm, weather_service,
    achievement_service, format_main_message, export_user_data
)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO if not config.DEBUG else logging.DEBUG
)
logger = logging.getLogger(__name__)

# Conversation states
(STATE_START, STATE_WEIGHT, STATE_HEIGHT, STATE_GENDER, STATE_ACTIVITY, 
 STATE_CITY, STATE_EDIT_WEIGHT, STATE_EDIT_HEIGHT, STATE_EDIT_CITY) = range(9)


# ============================================================================
# HELPERS
# ============================================================================

def get_lang(update: Update) -> str:
    user = get_user(update.effective_user.id)
    if user and user.language:
        return user.language
    return get_user_locale(update.effective_user.language_code)


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(update)
    user = get_user(user_id)
    
    if not user or not user.registration_complete:
        return await start_onboarding(update, context)
    
    today_ml = get_today_total(user_id)
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
            message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )


# ============================================================================
# START & ONBOARDING
# ============================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_locale(update.effective_user.language_code)
    
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
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    welcome_text = f"{L['welcome_title']}\n\n{L['welcome_text']}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(L["btn_start"], callback_data="start_registration")]
    ])
    
    await update.message.reply_text(welcome_text, reply_markup=keyboard)
    return STATE_START


async def onboarding_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user_id = update.effective_user.id
    
    try:
        weight = float(update.message.text)
        if not 30 <= weight <= 200:
            raise ValueError("Out of range")
        update_user(user_id, weight=weight)
        await update.message.reply_text(
            f"{L['reg_height']}\n\n_{L['reg_height_hint']}_",
            parse_mode=ParseMode.MARKDOWN
        )
        return STATE_HEIGHT
    except ValueError:
        await update.message.reply_text(L["error_range_weight"])
        return STATE_WEIGHT


async def process_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user_id = update.effective_user.id
    
    try:
        height = float(update.message.text)
        if not 100 <= height <= 250:
            raise ValueError("Out of range")
        update_user(user_id, height=height)
        await update.message.reply_text(L["reg_gender"], reply_markup=get_gender_keyboard(lang))
        return STATE_GENDER
    except ValueError:
        await update.message.reply_text(L["error_range_height"])
        return STATE_HEIGHT


async def process_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    user_id = update.effective_user.id
    
    await update.callback_query.answer()
    gender_str = update.callback_query.data.split("_")[1]
    gender = Gender(gender_str)
    update_user(user_id, gender=gender)
    
    L = Locale.RU if lang == "ru" else Locale.EN
    await update.callback_query.edit_message_text(
        L["reg_activity"], reply_markup=get_activity_keyboard(lang)
    )
    return STATE_ACTIVITY


async def process_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    user_id = update.effective_user.id
    
    await update.callback_query.answer()
    activity_str = update.callback_query.data.split("_")[1]
    activity = ActivityLevel(activity_str)
    # Устанавливаем дефолтный UTC, потом пользователь сам выберет
    update_user(user_id, activity_level=activity, timezone="UTC")
    
    L = Locale.RU if lang == "ru" else Locale.EN
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(L["reg_skip"], callback_data="skip_city")]
    ])
    
    await update.callback_query.edit_message_text(
        f"{L['reg_city']}\n\n_{L['reg_city_hint']}_",
        parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )
    return STATE_CITY


async def process_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    user_id = update.effective_user.id
    
    if update.callback_query:
        await update.callback_query.answer()
        if update.callback_query.data == "skip_city":
            return await complete_onboarding(update, context)
        return STATE_CITY
    
    city = update.message.text.strip()
    update_user(user_id, city=city)
    return await complete_onboarding(update, context)


async def complete_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    user = get_user(user_id)
    result = calculate_water_norm(weight=user.weight, gender=user.gender, activity_level=user.activity_level)
    complete_registration(user_id)
    
    await update.message.reply_text(f"{L['reg_complete']}\n\n{L['reg_complete_text'].format(norm=result.final_norm)}")
    return await send_main_menu(update, context)


async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(L["btn_cancel"])
    return ConversationHandler.END


# ============================================================================
# ADD WATER
# ============================================================================

async def cb_add_water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        L["add_water_title"], reply_markup=get_water_keyboard(lang)
    )


async def cb_water_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    data = update.callback_query.data
    
    if data == "water_custom":
        await update.callback_query.edit_message_text(
            f"{L['add_water_title']} ({L['add_custom']})",
            reply_markup=get_back_keyboard(lang, "add_water")
        )
        context.user_data["waiting_custom_volume"] = True
        return
    
    if data.startswith("water_"):
        volume = int(data.split("_")[1])
        context.user_data["pending_volume"] = volume
        await update.callback_query.edit_message_text(
            L["add_select_category"], reply_markup=get_drink_category_keyboard(lang)
        )


async def cb_drink_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор категории напитка"""
    lang = get_lang(update)
    
    await update.callback_query.answer()
    
    if update.callback_query.data == "drink_cat":
        L = Locale.RU if lang == "ru" else Locale.EN
        await update.callback_query.edit_message_text(
            L["add_select_category"], reply_markup=get_drink_category_keyboard(lang)
        )
        return
    
    category = update.callback_query.data.split("_")[1]  # cat_water, cat_coffee, etc.
    await update.callback_query.edit_message_text(
        Locale.get("add_select_drink", lang), 
        reply_markup=get_drink_type_keyboard(lang, category)
    )


async def cb_drink_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор конкретного напитка и запись"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    data = update.callback_query.data
    
    if data == "cancel":
        return await send_main_menu(update, context)
    
    if data.startswith("drink_"):
        # Используем maxsplit=1, так как типы напитков содержат underscore (tea_black, flat_white и т.д.)
        drink_type_str = data.split("_", 1)[1]
        drink_type = DrinkType(drink_type_str)
        volume = context.user_data.get("pending_volume", 250)
        coefficient = DRINK_COEFFICIENTS.get(drink_type, 1.0)
        effective = int(volume * coefficient)
        
        user = get_user(user_id)
        add_water_log(user_id, volume, drink_type, user.timezone if user else "UTC")
        
        # Check achievements
        new_achievements = await achievement_service.check_all_achievements(user_id, volume, drink_type)
        
        today_ml = get_today_total(user_id)
        goal_ml = get_user_daily_norm(user_id)
        old_level = user.level if user else 1
        
        if today_ml >= goal_ml:
            update_streak(user_id, True)
        
        user = get_user(user_id)
        new_level = user.level if user else 1
        
        # Success message
        success_text = f"✅ {L['add_success'].format(volume=volume, effective=effective)}"
        
        if new_level > old_level:
            success_text += f"\n\n🎊 {L['notif_level_up'].format(level=new_level)}"
        
        for ach_type in new_achievements:
            ach_info = achievement_service.get_achievement_info(ach_type, lang)
            rarity = ach_info.get("rarity", "common")
            
            if rarity == "mythic":
                ach_text = f"\n\n💎✨ {ach_info['name']} ✨💎\n🔴 +{ach_info['xp']} XP"
            elif rarity == "legendary":
                ach_text = f"\n\n🌟 {L['notif_achievement_legendary'].format(name=ach_info['name'])} 🌟\n🟡 +{ach_info['xp']} XP"
            elif rarity == "epic":
                ach_text = f"\n\n{ach_info['emoji']} **{ach_info['name']}**\n🟣 +{ach_info['xp']} XP"
            else:
                ach_text = f"\n\n{ach_info['rarity_emoji']} {ach_info['emoji']} {ach_info['name']}\n+{ach_info['xp']} XP"
            success_text += ach_text
        
        await update.callback_query.edit_message_text(success_text, parse_mode=ParseMode.MARKDOWN)
        await asyncio.sleep(1.5)
        return await send_main_menu(update, context)


async def handle_custom_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        await update.message.reply_text(
            L["add_select_category"], reply_markup=get_drink_category_keyboard(lang)
        )
    except ValueError:
        await update.message.reply_text(L["error_invalid_number"])


async def cb_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    return await send_main_menu(update, context)


# ============================================================================
# STATISTICS
# ============================================================================

async def cb_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "📊 " + ("Статистика" if lang == "ru" else "Statistics"),
        reply_markup=get_stats_keyboard(lang)
    )


async def cb_stats_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        text = f"📅 **{L['main_today']}**\n\n💧 {today_ml} / {goal_ml} мл\n📊 {min(percent, 100):.0f}%\n🔥 {user.current_streak or 0} {L['stats_days']}"
    
    elif period == "week":
        week_stats = get_week_stats(user_id, get_user_daily_norm(user_id))
        text = f"📆 **{'Неделя' if lang == 'ru' else 'Week'}**\n\n💧 {L['stats_total']}: {week_stats.total_ml} мл\n📊 {L['stats_average']}: {week_stats.average_ml:.0f} мл\n🔥 {L['stats_streak']}: {week_stats.streak} {L['stats_days']}"
        if week_stats.best_day:
            text += f"\n🏆 {L['stats_best_day']}: {week_stats.best_day.total_ml} мл"
    
    elif period == "month":
        heatmap = get_month_heatmap(user_id, get_user_daily_norm(user_id))
        total = sum(heatmap.values())
        text = f"🗓️ **{'Месяц' if lang == 'ru' else 'Month'}**\n\n💧 {L['stats_total']}: {total} мл\n📊 {L['stats_average']}: {total // 30:.0f} мл\n🔥 {L['stats_streak']}: {user.current_streak or 0} {L['stats_days']}"
    
    else:
        text = f"📊 **{'Год' if lang == 'ru' else 'Year'}**\n\n💧 {L['stats_total']}: {user.total_water_ml or 0} мл\n🏆 {L['stats_streak']}: {user.longest_streak or 0} {L['stats_days']}"
    
    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_back_keyboard(lang, "stats"))


# ============================================================================
# ACHIEVEMENTS
# ============================================================================

async def cb_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        for ach in achievements[:15]:
            ach_type = AchievementType(ach.achievement_type)
            info = achievement_service.get_achievement_info(ach_type, lang)
            date_str = ach.earned_at.strftime("%d.%m.%y") if ach.earned_at else ""
            rarity_emoji = info.get("rarity_emoji", "⚪")
            lines.append(f"{rarity_emoji} {info['emoji']} {info['name']} • {date_str}")
        
        if total_count > 15:
            lines.append(f"\n_... и ещё {total_count - 15}_")
        text = "\n".join(lines)
    
    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_back_keyboard(lang))


# ============================================================================
# ABOUT
# ============================================================================

async def cb_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.callback_query.answer()
    
    if lang == "ru":
        text = """💧 **Водный трекер**
_Твой персональный помощник для контроля водного баланса_

━━━━━━━━━━━━━━━━━━━━━━

**🎯 Возможности:**

**💧 Учёт напитков**
• Вода, минералка, газировка
• Чай: чёрный, зелёный, травяной, с молоком, матча
• Кофе: эспрессо, американо, капучино, латте, флэт уайт, мокка, айс кофе, колд брю
• Соки, смузи, молоко, газировка, энергетики

**📊 Расчёт нормы**
• Формула: вес × 30 мл × коэффициенты
• Учитывает пол, активность, погоду
• Коэффициенты гидратации для каждого напитка

**🏆 58 достижений**
• Серии: от 3 до 1000 дней
• Объём: от 5л до 10000л
• Временные, сезонные, секретные

**🎭 Режимы**
• 😊 Обычный | 💪 Тренировка (+30%)
• 🎯 Фокус | 🏖️ Отпуск (-20%)

━━━━━━━━━━━━━━━━━━━━━━

**📝 Коэффициенты:**
💧 Вода: 100% | 🍵 Чай: 85-95%
☕ Кофе: 65-90% | 🧃 Сок: 70%
⚡ Энергетик: 40%

━━━━━━━━━━━━━━━━━━━━━━

**💡 Совет:** Пейте воду регулярно в течение дня!

_Версия 1.0 | Создано с ❤️_"""
    else:
        text = """💧 **Water Tracker**
_Your personal hydration assistant_

━━━━━━━━━━━━━━━━━━━━━━

**🎯 Features:**

**💧 Drink Tracking**
• Water, sparkling, mineral
• Tea: black, green, herbal, milk, matcha
• Coffee: espresso, americano, cappuccino, latte, flat white, mocha, iced, cold brew
• Juices, smoothies, milk, soda, energy drinks

**📊 Goal Calculation**
• Formula: weight × 30ml × coefficients
• Based on gender, activity, weather
• Hydration coefficients for each drink

**🏆 58 Achievements**
• Streaks: from 3 to 1000 days
• Volume: from 5L to 10000L
• Time-based, seasonal, secret

**🎭 Modes**
• 😊 Normal | 💪 Workout (+30%)
• 🎯 Focus | 🏖️ Vacation (-20%)

━━━━━━━━━━━━━━━━━━━━━━

**📝 Coefficients:**
💧 Water: 100% | 🍵 Tea: 85-95%
☕ Coffee: 65-90% | 🧃 Juice: 70%
⚡ Energy: 40%

━━━━━━━━━━━━━━━━━━━━━━

**💡 Tip:** Drink water regularly throughout the day!

_Version 1.0 | Made with ❤️_"""
    
    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_back_keyboard(lang))


# ============================================================================
# SETTINGS
# ============================================================================

async def cb_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "⚙️ " + ("Настройки" if lang == "ru" else "Settings"),
        reply_markup=get_settings_keyboard(lang)
    )


async def cb_settings_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль с кнопками редактирования"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user = get_user(user_id)
    
    await update.callback_query.answer()
    
    text = (
        f"👤 **{L['profile_title']}**\n\n"
        f"⚖️ {L['profile_weight']}: {user.weight or '?'} кг\n"
        f"📏 {L['profile_height']}: {user.height or '?'} см\n"
        f"👤 {L['profile_gender']}: {str(user.gender.value) if user.gender else '?'}\n"
        f"🏃 {L['profile_activity']}: {str(user.activity_level.value) if user.activity_level else '?'}\n"
        f"🏙️ {L['profile_city']}: {user.city or '-'}\n"
    )
    
    await update.callback_query.edit_message_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_profile_keyboard(lang)
    )


async def cb_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать редактирование поля профиля"""
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    field = update.callback_query.data.split("_")[1]  # weight, height, city, etc.
    
    context.user_data["editing_field"] = field
    
    if field == "weight":
        await update.callback_query.edit_message_text(
            L["profile_edit_weight"], reply_markup=get_back_keyboard(lang, "settings_profile")
        )
        return STATE_EDIT_WEIGHT
    elif field == "height":
        await update.callback_query.edit_message_text(
            L["profile_edit_height"], reply_markup=get_back_keyboard(lang, "settings_profile")
        )
        return STATE_EDIT_HEIGHT
    elif field == "city":
        await update.callback_query.edit_message_text(
            L["profile_edit_city"], reply_markup=get_back_keyboard(lang, "settings_profile")
        )
        return STATE_EDIT_CITY
    elif field == "gender":
        await update.callback_query.edit_message_text(
            L["reg_gender"], reply_markup=get_gender_keyboard(lang)
        )
    elif field == "activity":
        await update.callback_query.edit_message_text(
            L["reg_activity"], reply_markup=get_activity_keyboard(lang)
        )
    
    return ConversationHandler.END


async def process_edit_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user_id = update.effective_user.id
    
    try:
        weight = float(update.message.text)
        if not 30 <= weight <= 200:
            raise ValueError()
        update_user(user_id, weight=weight)
        await update.message.reply_text(L["profile_updated"])
        return await cb_settings_profile(update, context)
    except ValueError:
        await update.message.reply_text(L["error_range_weight"])
        return STATE_EDIT_WEIGHT


async def process_edit_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user_id = update.effective_user.id
    
    try:
        height = float(update.message.text)
        if not 100 <= height <= 250:
            raise ValueError()
        update_user(user_id, height=height)
        await update.message.reply_text(L["profile_updated"])
        return await cb_settings_profile(update, context)
    except ValueError:
        await update.message.reply_text(L["error_range_height"])
        return STATE_EDIT_HEIGHT


async def process_edit_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user_id = update.effective_user.id
    
    city = update.message.text.strip()
    if city.lower() == "del":
        update_user(user_id, city=None)
    else:
        update_user(user_id, city=city)
    
    await update.message.reply_text(L["profile_updated"])
    return await cb_settings_profile(update, context)


async def cb_update_gender_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновить пол или активность из профиля"""
    user_id = update.effective_user.id
    lang = get_lang(update)
    
    await update.callback_query.answer()
    data = update.callback_query.data
    
    if data.startswith("gender_"):
        gender = Gender(data.split("_")[1])
        update_user(user_id, gender=gender)
    elif data.startswith("activity_"):
        activity = ActivityLevel(data.split("_")[1])
        update_user(user_id, activity_level=activity)
    
    return await cb_settings_profile(update, context)


async def cb_settings_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user = get_user(user_id)
    
    await update.callback_query.answer()
    
    status = "✅ " + ("Включены" if lang == "ru" else "Enabled") if user.notifications_enabled else "❌ " + ("Выключены" if lang == "ru" else "Disabled")
    time_range = f"{user.notification_start:02d}:00 - {user.notification_end:02d}:00"
    
    text = f"🔔 **{'Уведомления' if lang == 'ru' else 'Notifications'}**\n\n{'Статус' if lang == 'ru' else 'Status'}: {status}\n{'Время' if lang == 'ru' else 'Time'}: {time_range}\n"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 " + ("Выключить" if user.notifications_enabled else "Включить") if lang == "ru" else "🔔 " + ("Disable" if user.notifications_enabled else "Enable"), callback_data="toggle_notifications")],
        [
            InlineKeyboardButton("⏰ " + ("Начало" if lang == "ru" else "Start"), callback_data="set_notif_start"),
            InlineKeyboardButton("⏰ " + ("Конец" if lang == "ru" else "End"), callback_data="set_notif_end"),
        ],
        [InlineKeyboardButton(L["btn_back"], callback_data="settings")],
    ])
    
    await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


async def cb_toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    update_user(user_id, notifications_enabled=not user.notifications_enabled)
    return await cb_settings_notifications(update, context)


async def cb_set_notif_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.callback_query.answer()
    
    time_type = update.callback_query.data.split("_")[2]
    
    keyboard_rows = []
    row = []
    for hour in range(0, 24):
        row.append(InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"notif_time_{time_type}_{hour}"))
        if len(row) == 4:
            keyboard_rows.append(row)
            row = []
    if row:
        keyboard_rows.append(row)
    
    keyboard_rows.append([InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="settings_notifications")])
    
    if lang == "ru":
        text = f"⏰ {'Выберите время начала' if time_type == 'start' else 'Выберите время окончания'} уведомлений"
    else:
        text = f"⏰ Select {'start' if time_type == 'start' else 'end'} time for notifications"
    
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard_rows))


async def cb_save_notif_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.callback_query.answer()
    
    parts = update.callback_query.data.split("_")
    time_type = parts[2]
    hour = int(parts[3])
    
    if time_type == "start":
        update_user(user_id, notification_start=hour)
    else:
        update_user(user_id, notification_end=hour)
    
    return await cb_settings_notifications(update, context)


async def cb_settings_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        Locale.get("tz_select", lang), reply_markup=get_timezone_keyboard(lang)
    )


async def cb_set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    
    data = update.callback_query.data
    if data.startswith("tz_"):
        tz_name = data[3:] # Убираем префикс tz_
        update_user(user_id, timezone=tz_name)
        
        await update.callback_query.edit_message_text(
            L["tz_updated"], 
            reply_markup=get_back_keyboard(lang, "settings")
        )


async def cb_settings_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    mode_str = update.callback_query.data.split("_")[1]
    mode = ActivityMode(mode_str)
    update_user(user_id, activity_mode=mode)
    
    mode_labels = {"normal": L["mode_normal"], "workout": L["mode_workout"], "focus": L["mode_focus"], "vacation": L["mode_vacation"]}
    
    await update.callback_query.edit_message_text(L["mode_changed"].format(mode=mode_labels.get(mode_str, mode_str)))
    await asyncio.sleep(1)
    return await send_main_menu(update, context)


async def cb_settings_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    lang = str(user.language) if user and user.language else "ru"
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("🌐 Language / Язык", reply_markup=get_language_keyboard(lang))


async def cb_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.callback_query.answer()
    lang = update.callback_query.data.split("_")[1]
    update_user(user_id, language=lang)
    return await send_main_menu(update, context)


async def cb_settings_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "📤 " + ("Экспорт данных" if lang == "ru" else "Export Data"),
        reply_markup=get_export_keyboard(lang)
    )


async def cb_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    await update.callback_query.answer()
    format_type = update.callback_query.data.split("_")[1]
    
    content, filename = await export_user_data(user_id, format_type)
    
    from io import BytesIO
    file_bytes = BytesIO(content.encode('utf-8'))
    
    await context.bot.send_document(
        chat_id=user_id, document=file_bytes, filename=filename, caption=L["export_success"]
    )
    
    await update.callback_query.edit_message_text(L["export_success"], reply_markup=get_back_keyboard(lang, "settings"))


async def cb_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    return await send_main_menu(update, context)


# ============================================================================
# ERROR HANDLER
# ============================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
# SCHEDULED JOBS (NEW LOGIC)
# ============================================================================

def get_notification_keyboard(lang: str = "ru"):
    """Клавиатура для уведомлений с кнопкой 'Добавить напиток'"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton(Locale.get("main_add_water", lang), callback_data="add_water")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def job_minute_check(context: ContextTypes.DEFAULT_TYPE):
    """
    Запускается каждую минуту.
    Проверяет всех пользователей, вычисляет их локальное время.
    Если локальное время попадает в окно (Целевое время ± 2 минуты) — отправляет уведомление.
    """
    from database import get_session
    from models import User
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    # Кэш для хранения отметок "уже отправлено", чтобы не слать дубликаты в течение 4 минут
    # Формат: { (user_id, 'morning', '2023-10-27'): True }
    sent_cache = context.bot_data.setdefault('sent_notifications', set())

    session = get_session()
    try:
        # Берем только пользователей с включенными уведомлениями
        users = session.query(User).filter(
            User.notifications_enabled == True,
            User.registration_complete == True
        ).all()

        now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))

        for user in users:
            try:
                # 1. Определяем локальное время пользователя
                try:
                    tz = ZoneInfo(user.timezone or "UTC")
                except Exception:
                    tz = ZoneInfo("UTC")
                
                local_now = now_utc.astimezone(tz)
                local_time = local_now.time()
                local_date_str = local_now.strftime("%Y-%m-%d")
                
                lang = user.language or "ru"
                L = Locale.RU if lang == "ru" else Locale.EN
                
                # Список событий, которые нужно проверить для этого пользователя
                # Формат: (имя_события, целевой_час, целевая_минута)
                events_to_check = []

                # 1. Утреннее уведомление (время старта)
                events_to_check.append(("morning", user.notification_start, 0))

                # 2. Вечерний отчет (за час до конца или в 21:00)
                evening_hour = user.notification_end - 1
                if evening_hour < user.notification_start:
                    evening_hour = 21
                events_to_check.append(("evening", evening_hour, 0))

                # 3. Напоминания (каждые 2 часа после старта)
                # Например, старт 8. Напоминания: 10, 12, 14...
                rem_h = user.notification_start + 2
                while rem_h < evening_hour:
                    events_to_check.append((f"reminder_{rem_h}", rem_h, 0))
                    rem_h += 2

                # Проверяем каждое событие
                for event_name, target_hour, target_minute in events_to_check:
                    target_time = datetime(local_now.year, local_now.month, local_now.day, target_hour, target_minute, 0, tzinfo=tz).time()
                    
                    # Вычисляем разницу во времени
                    current_minutes = local_time.hour * 60 + local_time.minute
                    target_minutes = target_time.hour * 60 + target_time.minute
                    
                    # Окно: ± 2 минуты (от -2 до +2)
                    diff = current_minutes - target_minutes
                    
                    if -2 <= diff <= 2:
                        # Ключ для кэша (уникальный для каждого события в день)
                        cache_key = (user.id, event_name, local_date_str)
                        
                        if cache_key not in sent_cache:
                            # Отправляем уведомление
                            await process_notification_event(user, event_name, context, lang, L)
                            
                            # Ставим отметку, что отправили
                            sent_cache.add(cache_key)

            except Exception as e:
                logger.error(f"Error checking notifications for user {user.id}: {e}")

        # Чистим старые записи из кэша (раз в час), чтобы память не засорялась
        if now_utc.minute == 0:
            # Удаляем ключи, которые не относятся к текущему дню (упрощенно)
            context.bot_data['sent_notifications'] = {
                k for k in sent_cache if local_date_str in str(k)
            }

    finally:
        session.close()


async def process_notification_event(user, event_name: str, context: ContextTypes.DEFAULT_TYPE, lang: str, L: Dict):
    """Вспомогательная функция отправки конкретного уведомления"""
    try:
        text = ""
        
        # Логика для разных типов уведомлений
        if event_name == "morning":
            today_ml = get_today_total(user.id)
            goal_ml = get_user_daily_norm(user.id)
            weather_text = ""
            if user.city:
                weather = await weather_service.get_weather(user.city)
                if weather:
                    weather_text = f"{weather.temperature:.0f}°C, {weather.description}"
            
            text = L["notif_morning"].format(weather=weather_text or ("нет данных" if lang == "ru" else "N/A"), norm=goal_ml)

        elif event_name == "evening":
            today_ml = get_today_total(user.id)
            goal_ml = get_user_daily_norm(user.id)
            percent = min(100, round((today_ml / goal_ml) * 100) if goal_ml > 0 else 0)
            text = L["notif_evening"].format(current=today_ml, goal=goal_ml, percent=percent)

        elif event_name.startswith("reminder_"):
            today_ml = get_today_total(user.id)
            goal_ml = get_user_daily_norm(user.id)
            remaining = max(0, goal_ml - today_ml)
            
            if remaining <= 0:
                return # Не шлем напоминание, если норма выполнена
            
            text = L["notif_reminder"].format(remaining=remaining)
        
        # Отправка
        if text:
            keyboard = get_notification_keyboard(lang)
            await context.bot.send_message(user.id, text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Failed to send notification {event_name} to user {user.id}: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    init_database()
    
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is required!")
        print("\n❌ Error: BOT_TOKEN is not set!\n")
        return
    
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Conversation handler
    onboarding_handler = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            STATE_START: [CallbackQueryHandler(onboarding_weight, pattern="^start_registration$")],
            STATE_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_weight)],
            STATE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_height)],
            STATE_GENDER: [CallbackQueryHandler(process_gender, pattern="^gender_")],
            STATE_ACTIVITY: [CallbackQueryHandler(process_activity, pattern="^activity_")],
            STATE_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_city),
                CallbackQueryHandler(process_city, pattern="^skip_city$")
            ],
            STATE_EDIT_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_weight)],
            STATE_EDIT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_height)],
            STATE_EDIT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_edit_city)],
        },
        fallbacks=[CallbackQueryHandler(cancel_onboarding, pattern="^cancel$")],
        per_user=True, per_chat=True,
    )
    
    application.add_handler(onboarding_handler)
    
    # Main menu
    application.add_handler(CallbackQueryHandler(cb_main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(cb_add_water, pattern="^add_water$"))
    application.add_handler(CallbackQueryHandler(cb_water_volume, pattern="^water_"))
    application.add_handler(CallbackQueryHandler(cb_drink_category, pattern="^cat_"))
    application.add_handler(CallbackQueryHandler(cb_drink_category, pattern="^drink_cat$"))
    application.add_handler(CallbackQueryHandler(cb_drink_type, pattern="^drink_"))
    
    # Custom volume
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_volume))
    
    # Stats & Achievements
    application.add_handler(CallbackQueryHandler(cb_stats, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(cb_stats_period, pattern="^stats_"))
    application.add_handler(CallbackQueryHandler(cb_achievements, pattern="^achievements$"))
    application.add_handler(CallbackQueryHandler(cb_about, pattern="^about$"))
    
    # Settings
    application.add_handler(CallbackQueryHandler(cb_settings, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(cb_settings_profile, pattern="^settings_profile$"))
    application.add_handler(CallbackQueryHandler(cb_edit_field, pattern="^edit_"))
    application.add_handler(CallbackQueryHandler(cb_update_gender_activity, pattern="^gender_"))
    application.add_handler(CallbackQueryHandler(cb_update_gender_activity, pattern="^activity_"))
    application.add_handler(CallbackQueryHandler(cb_settings_notifications, pattern="^settings_notifications$"))
    application.add_handler(CallbackQueryHandler(cb_toggle_notifications, pattern="^toggle_notifications$"))
    application.add_handler(CallbackQueryHandler(cb_set_notif_time, pattern="^set_notif_"))
    application.add_handler(CallbackQueryHandler(cb_save_notif_time, pattern="^notif_time_"))
    application.add_handler(CallbackQueryHandler(cb_settings_timezone, pattern="^settings_timezone$"))
    application.add_handler(CallbackQueryHandler(cb_set_timezone, pattern="^tz_"))
    application.add_handler(CallbackQueryHandler(cb_settings_mode, pattern="^settings_mode$"))
    application.add_handler(CallbackQueryHandler(cb_set_mode, pattern="^mode_"))
    application.add_handler(CallbackQueryHandler(cb_settings_language, pattern="^settings_language$"))
    application.add_handler(CallbackQueryHandler(cb_set_language, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(cb_settings_export, pattern="^settings_export$"))
    application.add_handler(CallbackQueryHandler(cb_export_data, pattern="^export_"))
    
    application.add_handler(CallbackQueryHandler(cb_cancel, pattern="^cancel$"))
    application.add_error_handler(error_handler)
    
    # Job queue
    job_queue = application.job_queue
    if job_queue:
        # Запускаем проверку каждую минуту
        # first=1 означает задержку в 1 секунду перед первым запуском
        job_queue.run_repeating(
            job_minute_check, 
            interval=60, # Каждые 60 секунд
            first=1
        )
        logger.info("JobQueue initialized with minute checks (timezone-aware, fuzzy window ±2 min)")
    else:
        logger.warning("JobQueue not available")
    
    print("\n💧 WaterBot is starting...")
    print("=" * 40)
    print("Bot is ready! Send /start to begin.")
    print("=" * 40 + "\n")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()