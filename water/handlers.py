"""
Handlers for water tracking functionality
"""

import asyncio
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import Locale, DrinkType
from db import (
    add_water_log, get_today_total, get_user,
    update_streak, reschedule_smart_notifications,
    get_favorite_volumes, add_favorite_volume
)
from services import (
    get_user_daily_norm,
    achievement_service,
)
from water.keyboards import (
    get_water_keyboard,
    get_drink_category_keyboard,
    get_drink_type_keyboard,
    get_quick_add_keyboard
)
from water.utils import (
    format_success_message,
    validate_custom_volume,
    check_daily_goal_completion,
    get_available_volumes,
    update_favorite_volume
)
from water.constants import WATER_PRESETS
from common.decorators import require_registration
from common.helpers import get_user_locale, safe_send_message

logger = logging.getLogger(__name__)


async def format_main_message(current_ml, goal_ml, streak, temperature, weather_desc, lang):
    """Placeholder for format_main_message function"""
    percent = round((current_ml / goal_ml) * 100, 1) if goal_ml > 0 else 0
    bar = get_progress_bar(current_ml, goal_ml)
    
    text = f"💧 **Сегодня**\n\n{bar}\n**{current_ml}** / {goal_ml} мл ({percent}%)"
    
    if streak > 0:
        text += f"\n\n🔥 {streak} дней"
    
    return text


def get_progress_bar(current, goal, width=10):
    """Generate progress bar"""
    if goal <= 0:
        return "░" * width
    
    percent = min(current / goal, 1.0)
    filled = int(percent * width)
    
    if percent >= 1.0:
        return "█" * width
    else:
        return "█" * filled + "░" * (width - filled)


@require_registration
async def cb_add_water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show water volume selection"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    # Get user's favorite volumes for quick add
    user_id = update.effective_user.id
    favorites = await get_favorite_volumes(user_id)
    
    await query.edit_message_text(
        L["add_water_title"],
        reply_markup=get_water_keyboard(lang)
    )


@require_registration
async def cb_water_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle volume selection"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    data = query.data
    
    if data == "water_custom":
        # Ask for custom volume
        context.user_data["waiting_custom_volume"] = True
        await query.edit_message_text(
            f"{L['add_water_title']} ({L['add_custom']})",
            reply_markup=None
        )
        return
    
    if data.startswith("water_"):
        # Store selected volume
        volume = int(data.split("_")[1])
        context.user_data["pending_volume"] = volume
        
        # Show drink categories
        await query.edit_message_text(
            L["add_select_category"],
            reply_markup=get_drink_category_keyboard(lang)
        )


@require_registration
async def cb_drink_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle drink category selection"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    data = query.data
    
    if data == "drink_cat":
        # Back to category selection
        L = Locale.RU if lang == "ru" else Locale.EN
        await query.edit_message_text(
            L["add_select_category"],
            reply_markup=get_drink_category_keyboard(lang)
        )
        return
    
    if data.startswith("cat_"):
        # Show drinks for selected category
        category = data.split("_")[1]
        await query.edit_message_text(
            Locale.get("add_select_drink", lang),
            reply_markup=get_drink_type_keyboard(lang, category)
        )


@require_registration
async def cb_drink_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle final drink selection and save log"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    data = query.data
    
    if data.startswith("drink_"):
        drink_type_str = data.split("_", 1)[1]
        drink_type = DrinkType(drink_type_str)
        
        # Get pending volume
        volume = context.user_data.get("pending_volume", 250)
        
        # Clear pending data
        context.user_data.pop("pending_volume", None)
        
        # Get user for timezone
        user = await get_user(user_id)
        timezone = user.timezone if user else "UTC"
        
        # Add water log
        log = await add_water_log(
            user_id=user_id,
            volume_ml=volume,
            drink_type=drink_type,
            timezone=timezone
        )
        
        # Reschedule notifications (today_total changed)
        await reschedule_smart_notifications(user_id)
        
        # Check achievements
        new_achievements = await achievement_service.check_all_achievements(
            user_id, volume, drink_type
        )
        
        # Check if daily goal reached
        goal_reached, today_total, goal = await check_daily_goal_completion(user_id)
        if goal_reached:
            await update_streak(user_id, True)
        
        # Get updated user for level info
        user = await get_user(user_id)
        old_level = context.user_data.get("last_level", 1)
        new_level = user.level if user else 1
        
        # Format success message
        success_text = format_success_message(
            volume=volume,
            effective=log.effective_ml,
            drink_type=drink_type,
            lang=lang
        )
        
        # Add level up notification
        if new_level > old_level:
            L = Locale.RU if lang == "ru" else Locale.EN
            success_text += f"\n\n🎊 {L['notif_level_up'].format(level=new_level)}"
        
        # Add achievement notifications
        for ach_type in new_achievements:
            ach_info = achievement_service.get_achievement_info(ach_type, lang)
            rarity = ach_info.get("rarity", "common")
            
            if rarity == "mythic":
                ach_text = f"\n\n💎✨ {ach_info['name']} ✨💎\n🔴 +{ach_info['xp']} XP"
            elif rarity == "legendary":
                ach_text = f"\n\n🌟 {ach_info['name']} 🌟\n🟡 +{ach_info['xp']} XP"
            elif rarity == "epic":
                ach_text = f"\n\n{ach_info['emoji']} **{ach_info['name']}**\n🟣 +{ach_info['xp']} XP"
            else:
                ach_text = f"\n\n{ach_info['rarity_emoji']} {ach_info['emoji']} {ach_info['name']}\n+{ach_info['xp']} XP"
            
            success_text += ach_text
        
        # Update last known level
        context.user_data["last_level"] = new_level
        
        # Ask if user wants to add this volume to favorites
        if volume not in WATER_PRESETS:
            favorites = await get_favorite_volumes(user_id)
            if volume not in favorites:
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "⭐ " + ("Добавить в избранное", "Add to favorites")[lang == "en"],
                        callback_data=f"fav_add_{volume}"
                    )
                ]])
                
                await query.edit_message_text(
                    success_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                await asyncio.sleep(1.5)
        
        # Show success message and return to main menu
        await query.edit_message_text(
            success_text,
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(2)
        
        # Return to main menu
        # from bot.handlers import send_main_menu
        # await send_main_menu(update, context)


async def handle_custom_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom volume input"""
    if not context.user_data.get("waiting_custom_volume"):
        return
    
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    # Validate volume
    is_valid, volume, error_key = validate_custom_volume(update.message.text)
    
    if not is_valid:
        await update.message.reply_text(L[error_key])
        return
    
    # Store volume and clear waiting flag
    context.user_data["pending_volume"] = volume
    context.user_data["waiting_custom_volume"] = False
    
    # Show drink categories
    await update.message.reply_text(
        L["add_select_category"],
        reply_markup=get_drink_category_keyboard(lang)
    )


@require_registration
async def cb_add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add current volume to favorites"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    data = query.data
    if data.startswith("fav_add_"):
        volume = int(data.split("_")[2])
        
        # Add to favorites
        await update_favorite_volume(user_id, volume)
        
        L = Locale.RU if lang == "ru" else Locale.EN
        await query.edit_message_text(
            f"⭐ {L.get('fav_added', 'Добавлено в избранное!')}"
        )
        
        await asyncio.sleep(1)
        
        # Return to main menu
        # from bot.handlers import send_main_menu
        # await send_main_menu(update, context)


@require_registration
async def cb_quick_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick add with default drink type (water)"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    data = query.data.split("_")
    # format: quick_250_water
    volume = int(data[1])
    drink_type_str = data[2]
    drink_type = DrinkType(drink_type_str)
    
    # Get user for timezone
    user = await get_user(user_id)
    timezone = user.timezone if user else "UTC"
    
    # Add water log
    log = await add_water_log(
        user_id=user_id,
        volume_ml=volume,
        drink_type=drink_type,
        timezone=timezone
    )
    
    # Reschedule notifications
    await reschedule_smart_notifications(user_id)
    
    # Check achievements
    new_achievements = await achievement_service.check_all_achievements(
        user_id, volume, drink_type
    )
    
    # Format quick success message
    L = Locale.RU if lang == "ru" else Locale.EN
    success_text = f"✅ {volume} мл"
    
    if new_achievements:
        success_text += "\n\n" + L.get("new_achievements", "Новые достижения!")
    
    await query.edit_message_text(success_text)
    
    await asyncio.sleep(1)
    
    # Return to main menu
    # from bot.handlers import send_main_menu
    # await send_main_menu(update, context)