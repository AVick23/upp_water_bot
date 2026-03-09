"""
Handlers for achievements module
"""

import asyncio
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import Locale, AchievementType
from db import (
    get_user_achievements, get_user, has_achievement,
    get_achievements_count
)
from services import achievement_service
from achievements.keyboards import (
    get_achievements_main_keyboard,
    get_category_keyboard,
    get_rarity_keyboard,
    get_achievement_detail_keyboard,
    get_achievement_share_keyboard,
    get_achievement_progress_keyboard
)
from achievements.utils import (
    get_user_achievements_data,
    get_achievement_progress,
    get_next_achievements,
    format_achievement_text,
    format_achievement_unlock,
    get_rarity_stats,
    get_recent_achievements
)
from achievements.constants import STATS_MESSAGES, RARITY_DISPLAY
from common.decorators import require_registration
from common.helpers import get_user_locale, safe_send_message, get_progress_bar

logger = logging.getLogger(__name__)


@require_registration
async def cb_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show achievements main menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    # Get user achievements data
    data = await get_user_achievements_data(user_id)
    
    # Get recent achievements separately
    achievements = await get_user_achievements(user_id)
    recent = get_recent_achievements(achievements, days=30, limit=5)
    
    # Format main text
    text = format_achievements_main(data, recent, lang)  # Pass recent as parameter
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_achievements_main_keyboard(lang)
    )


def format_achievements_main(data: dict, recent: list, lang: str) -> str:
    """Format main achievements menu text (synchronous)"""
    from achievements.constants import STATS_MESSAGES, RARITY_DISPLAY
    
    messages = STATS_MESSAGES["ru"] if lang == "ru" else STATS_MESSAGES["en"]
    
    text = [
        f"🏆 **{messages['title']}**",
        "",
        f"📊 {messages['total'].format(count=data['total_earned'])} / {data['total_possible']}",
        f"🎯 {messages['completion'].format(percent=data['completion_percent'])}",
        f"✨ {messages['total_xp'].format(xp=data['total_xp'])}",
        f"⭐ {messages['level'].format(level=data['level'])}",
        "",
    ]
    
    # Add rarity breakdown
    if data['by_rarity']:
        text.append(f"**{messages['by_rarity']}**")
        rarity_stats = get_rarity_stats(data['by_rarity'])
        
        for rarity, stats in sorted(rarity_stats.items(), 
                                   key=lambda x: RARITY_DISPLAY[x[0]]["order"]):
            if stats['total'] > 0:
                text.append(
                    f"{stats['emoji']} {stats[f'name_{lang}']}: "
                    f"{stats['earned']}/{stats['total']} ({stats['percent']}%)"
                )
        text.append("")
    
    # Add recent achievements
    if recent:
        text.append(f"**{messages['recent']}**")
        for ach in recent:
            date_str = ach['earned_at'].strftime("%d.%m")
            text.append(f"{ach['info']['emoji']} {ach['info']['name']} • {date_str}")
    
    return "\n".join(text)


@require_registration
async def cb_achievement_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show achievements by category"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    category_id = query.data.split("_")[2]  # ach_cat_{category}
    
    # Get user's earned achievements
    earned = await get_user_achievements(user_id)
    earned_ids = [a.achievement_type.value for a in earned]
    
    # Get category info
    from achievements.constants import ACHIEVEMENT_CATEGORIES
    category = ACHIEVEMENT_CATEGORIES.get(category_id, {})
    
    text = f"**{category['icon']} {category[f'name_{lang}']}**\n\n"
    
    # Add category description
    desc_key = f"cat_{category_id}_desc"
    desc = Locale.get(desc_key, lang)
    if desc != desc_key:
        text += f"_{desc}_\n\n"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_category_keyboard(category_id, earned_ids, lang)
    )


@require_registration
async def cb_achievement_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show achievement details"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    ach_id = query.data.split("_")[2]  # ach_detail_{id}
    
    # Find achievement type
    ach_type = None
    for a in AchievementType:
        if a.value == ach_id:
            ach_type = a
            break
    
    if not ach_type:
        await query.edit_message_text("❌ Achievement not found")
        return
    
    # Check if earned
    earned = await has_achievement(user_id, ach_type)
    
    # Get progress
    progress = await get_achievement_progress(user_id, ach_type)
    
    # Format text
    text = format_achievement_text(ach_type, earned, progress, lang)
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_achievement_detail_keyboard(ach_type, earned, lang)
    )


@require_registration
async def cb_achievement_rarity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show achievements by rarity"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    rarity = query.data.split("_")[2]  # ach_rarity_{rarity}
    
    # Get user's earned achievements
    earned = await get_user_achievements(user_id)
    earned_ids = [a.achievement_type.value for a in earned]
    
    # Get rarity info
    from achievements.constants import RARITY_DISPLAY
    rarity_info = RARITY_DISPLAY.get(rarity, {})
    
    text = f"{rarity_info['emoji']} **{rarity_info[f'name_{lang}']}**"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_rarity_keyboard(rarity, earned_ids, lang)
    )


@require_registration
async def cb_achievement_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show achievement statistics"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    data = await get_user_achievements_data(user_id)
    messages = STATS_MESSAGES["ru"] if lang == "ru" else STATS_MESSAGES["en"]
    
    text = [
        f"📊 **{messages['title']} Statistics**",
        "",
        f"📈 {messages['completion'].format(percent=data['completion_percent'])}",
        f"✨ {messages['total_xp'].format(xp=data['total_xp'])}",
        f"⭐ {messages['level'].format(level=data['level'])}",
        "",
    ]
    
    # Next achievements
    next_achs = await get_next_achievements(user_id, 3)
    if next_achs:
        text.append("🎯 **" + ("Ближайшие:", "Next up:")[lang == "en"] + "**")
        for ach in next_achs:
            info = ach['info']
            text.append(
                f"{info['emoji']} {ach['percent']}% "
                f"({ach['progress']}/{ach['target']})"
            )
    
    await query.edit_message_text(
        "\n".join(text),
        parse_mode="Markdown",
        reply_markup=get_achievement_progress_keyboard(lang)
    )


@require_registration
async def cb_achievement_recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent achievements"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    achievements = await get_user_achievements(user_id)
    recent = get_recent_achievements(achievements, days=30, limit=10)
    
    if not recent:
        text = "📅 " + ("Нет недавних достижений", "No recent achievements")[lang == "en"]
    else:
        text = "**📅 " + ("Недавние достижения", "Recent achievements")[lang == "en"] + "**\n\n"
        
        for ach in recent:
            date_str = ach['earned_at'].strftime("%d.%m.%Y")
            info = ach['info']
            text += f"{info['emoji']} {info['name']} • {date_str}\n"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_achievements_main_keyboard(lang)
    )


@require_registration
async def cb_achievement_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Share achievement"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    ach_id = query.data.split("_")[2]  # ach_share_{id}
    
    # Find achievement type
    ach_type = None
    for a in AchievementType:
        if a.value == ach_id:
            ach_type = a
            break
    
    if not ach_type:
        await query.edit_message_text("❌ Achievement not found")
        return
    
    # Get achievement info
    from config import ACHIEVEMENTS, Locale
    info = ACHIEVEMENTS.get(ach_type, {})
    name = Locale.get(f"ach_{ach_type.value}", lang)
    
    # Create share text
    share_text = (
        f"🏆 Я получил достижение '{name}' в WaterBot!\n"
        f"{info['emoji']} +{info.get('xp', 0)} XP\n"
        f"#WaterBot #Достижение"
    )
    
    context.user_data["share_text"] = share_text
    
    await query.edit_message_text(
        f"📢 **" + ("Поделиться достижением", "Share achievement")[lang == "en"] + "**\n\n"
        f"```\n{share_text}\n```\n\n"
        "_" + ("Нажмите кнопку ниже, чтобы скопировать", "Press the button below to copy")[lang == "en"] + "_",
        parse_mode="Markdown",
        reply_markup=get_achievement_share_keyboard(ach_type, lang)
    )


@require_registration
async def cb_achievement_share_copy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Copy share text to clipboard (via message)"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    share_text = context.user_data.get("share_text", "")
    
    if share_text:
        # Send as separate message for easy copying
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=f"```\n{share_text}\n```",
            parse_mode="Markdown"
        )
        
        await query.edit_message_text(
            "✅ " + ("Текст скопирован!", "Text copied!")[lang == "en"],
            reply_markup=get_achievements_main_keyboard(lang)
        )
    else:
        await query.edit_message_text(
            "❌ " + ("Ошибка", "Error")[lang == "en"],
            reply_markup=get_achievements_main_keyboard(lang)
        )


@require_registration
async def cb_achievement_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track achievement progress"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    ach_id = query.data.split("_")[2]  # ach_track_{id}
    
    # Find achievement type
    ach_type = None
    for a in AchievementType:
        if a.value == ach_id:
            ach_type = a
            break
    
    if not ach_type:
        await query.edit_message_text("❌ Achievement not found")
        return
    
    # Set tracking in user data
    if "tracking_achievements" not in context.user_data:
        context.user_data["tracking_achievements"] = []
    
    if ach_id not in context.user_data["tracking_achievements"]:
        context.user_data["tracking_achievements"].append(ach_id)
        text = "✅ " + ("Достижение добавлено в отслеживание", "Achievement added to tracking")[lang == "en"]
    else:
        text = "ℹ️ " + ("Уже отслеживается", "Already tracking")[lang == "en"]
    
    await query.edit_message_text(
        text,
        reply_markup=get_achievement_detail_keyboard(ach_type, False, lang)
    )


@require_registration
async def cb_achievement_progress_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all achievement progress"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    data = await get_user_achievements_data(user_id)
    next_achs = await get_next_achievements(user_id, 10)
    
    text = "**📊 " + ("Общий прогресс", "Overall progress")[lang == "en"] + "**\n\n"
    
    # Overall stats
    text += f"🏆 {data['total_earned']}/{data['total_possible']} ({data['completion_percent']}%)\n\n"
    
    # Next achievements
    if next_achs:
        text += "**🎯 " + ("Следующие:", "Next achievements:")[lang == "en"] + "**\n"
        for ach in next_achs[:5]:
            info = ach['info']
            bar = get_progress_bar(ach['progress'], ach['target'], 5)
            text += f"{info['emoji']} {bar} {ach['percent']}%\n"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_achievement_progress_keyboard(lang)
    )