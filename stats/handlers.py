"""
Handlers for statistics module
"""

import asyncio
import logging
from datetime import date, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import Locale
from db import (
    get_user_stats, get_week_stats, get_month_heatmap,
    get_user, get_achievements_count, get_user_achievements,
    export_to_dict, export_to_csv
)
from services import get_user_daily_norm, get_user_daily_norm_sync, achievement_service
from stats.keyboards import (
    get_stats_keyboard, get_detailed_stats_keyboard,
    get_comparison_keyboard, get_heatmap_keyboard,
    get_export_keyboard
)
from stats.utils import (
    get_period_data, format_heatmap, format_time_distribution,
    get_time_distribution, get_weekday_distribution,
    format_weekday_distribution, compare_periods
)
from common.decorators import require_registration
from common.helpers import get_user_locale, safe_send_message, format_number

logger = logging.getLogger(__name__)


@require_registration
async def cb_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics menu"""
    query = update.callback_query
    await query.answer()
    
    lang = get_user_locale(update)
    
    await query.edit_message_text(
        "📊 " + ("Статистика" if lang == "ru" else "Statistics"),
        reply_markup=get_stats_keyboard(lang)
    )


@require_registration
async def cb_stats_period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics for specific period"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    data = query.data.split("_")
    period = data[1]  # day, week, month, year, all
    
    # Check if date is specified (for navigation)
    target_date = date.today()
    if len(data) > 2:
        try:
            target_date = date.fromisoformat(data[2])
        except:
            target_date = date.today()
    
    # Get period data
    period_data = await get_period_data(user_id, period, target_date)
    
    # Get user for goal
    user = await get_user(user_id)
    daily_goal = get_user_daily_norm_sync(user_id)
    
    # Format message based on period
    if period == "day":
        text = format_day_stats(user_id, period_data, daily_goal, lang)
    elif period == "week":
        text = await format_week_stats(user_id, period_data, daily_goal, lang)
    elif period == "month":
        text = await format_month_stats(user_id, period_data, daily_goal, lang)
    else:  # all time
        text = await format_all_time_stats(user_id, period_data, daily_goal, lang)
    
    # Add navigation keyboard for week/month
    keyboard = get_detailed_stats_keyboard(period, target_date, lang)
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


def format_day_stats(user_id: int, data: dict, goal: int, lang: str) -> str:
    """Format daily statistics"""
    L = Locale.RU if lang == "ru" else Locale.EN
    
    date_str = data["end_date"].strftime("%d.%m.%Y")
    percent = (data["total_ml"] / goal * 100) if goal > 0 else 0
    
    from services import get_progress_bar
    bar = get_progress_bar(data["total_ml"], goal)
    
    text = (
        f"📅 **{date_str}**\n\n"
        f"{bar}\n"
        f"💧 {data['total_ml']} / {goal} мл ({percent:.0f}%)\n"
    )
    
    # Add comparison to average
    week_avg = data.get("average_ml", 0)
    if week_avg > 0:
        diff = data["total_ml"] - week_avg
        if diff > 0:
            text += f"📈 +{diff} мл к среднему за неделю\n"
        elif diff < 0:
            text += f"📉 {diff} мл к среднему за неделю\n"
    
    return text


async def format_week_stats(user_id: int, data: dict, goal: int, lang: str) -> str:
    """Format weekly statistics"""
    L = Locale.RU if lang == "ru" else Locale.EN
    
    week_stats = await get_week_stats(user_id, goal)
    
    text = (
        f"📆 **{L['stats_week']}**\n"
        f"{data['start_date'].strftime('%d.%m')} - {data['end_date'].strftime('%d.%m')}\n\n"
        f"💧 {L['stats_total']}: {format_number(data['total_ml'], lang)} мл\n"
        f"📊 {L['stats_average']}: {format_number(data['average_ml'], lang)} мл/день\n"
        f"🔥 {L['stats_streak']}: {week_stats['streak']} {L['stats_days']}\n"
    )
    
    if data['best_day']:
        text += f"🏆 {L['stats_best_day']}: {data['best_value']} мл ({data['best_day'].strftime('%d.%m')})\n"
    
    # Add daily breakdown
    text += "\n**" + ("По дням:" if lang == "ru" else "Daily:") + "**\n"
    for day_data in week_stats['days'][:7]:
        day_name = day_data['date'].strftime('%a')[0:2]
        bar = get_progress_bar(day_data['total_ml'], goal, 5)
        text += f"{day_name}: {bar} {day_data['total_ml']} мл\n"
    
    return text


async def format_month_stats(user_id: int, data: dict, goal: int, lang: str) -> str:
    """Format monthly statistics"""
    L = Locale.RU if lang == "ru" else Locale.EN
    
    # Get heatmap
    heatmap = await get_month_heatmap(user_id, goal)
    
    text = (
        f"🗓️ **{L['stats_month']}**\n"
        f"{data['start_date'].strftime('%d.%m')} - {data['end_date'].strftime('%d.%m')}\n\n"
        f"💧 {L['stats_total']}: {format_number(data['total_ml'], lang)} мл\n"
        f"📊 {L['stats_average']}: {format_number(data['average_ml'], lang)} мл/день\n"
        f"📅 {L['stats_active_days']}: {data['active_days']} / {data['total_days']} "
        f"({(data['active_days']/data['total_days']*100):.0f}%)\n\n"
    )
    
    # Add heatmap
    if heatmap:
        text += "**" + ("Тепловая карта:" if lang == "ru" else "Heatmap:") + "**\n"
        text += "```\n"
        # Simple heatmap representation
        days = sorted(heatmap.keys())
        week = []
        for d in days:
            level = heatmap[d] // 25  # 0-4
            symbols = ["░", "▒", "▓", "█", "█"]
            week.append(symbols[min(level, 4)])
            if len(week) == 7:
                text += "".join(week) + "\n"
                week = []
        if week:
            text += "".join(week) + "\n"
        text += "```\n"
        text += "░ <25% ▒ 25-50% ▓ 50-75% █ >75%\n"
    
    return text


async def format_all_time_stats(user_id: int, data: dict, goal: int, lang: str) -> str:
    """Format all-time statistics"""
    L = Locale.RU if lang == "ru" else Locale.EN
    user = await get_user(user_id)
    
    achievements_count = await get_achievements_count(user_id)
    
    text = (
        f"💫 **{L['stats_all_time']}**\n\n"
        f"💧 {L['stats_total']}: {format_number(user.total_water_ml or 0, lang)} мл\n"
        f"📅 {L['stats_active_days']}: {data['active_days']} {L['stats_days']}\n"
        f"🔥 {L['stats_best_streak']}: {user.longest_streak or 0} {L['stats_days']}\n"
        f"🏆 {L['stats_achievements']}: {achievements_count}\n"
        f"⭐ {L['stats_level']}: {user.level or 1} ({user.xp or 0} XP)\n"
    )
    
    if data['best_day']:
        text += f"🌟 {L['stats_best_day']}: {data['best_value']} мл ({data['best_day'].strftime('%d.%m.%Y')})\n"
    
    return text


@require_registration
async def cb_stats_trends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show trends and patterns"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    
    # Get time distribution
    time_dist = await get_time_distribution(user_id)
    time_text = format_time_distribution(time_dist, lang)
    
    # Get weekday distribution
    weekday_dist = await get_weekday_distribution(user_id)
    weekday_text = format_weekday_distribution(weekday_dist, lang)
    
    text = f"{time_text}\n\n{weekday_text}"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_comparison_keyboard(lang)
    )


@require_registration
async def cb_stats_streaks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show streak statistics"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    user = await get_user(user_id)
    
    # Get streak achievements
    achievements = await get_user_achievements(user_id)
    streak_achievements = []
    for ach in achievements:
        if "streak" in ach.achievement_type.value:
            streak_achievements.append(ach)
    
    text = (
        f"🔥 **{L['stats_streaks']}**\n\n"
        f"📅 {L['stats_current_streak']}: {user.current_streak or 0} {L['stats_days']}\n"
        f"🏆 {L['stats_best_streak']}: {user.longest_streak or 0} {L['stats_days']}\n\n"
    )
    
    if streak_achievements:
        text += "**" + (L['stats_streak_achievements'] if hasattr(L, 'stats_streak_achievements') else "Достижения за серии:") + "**\n"
        for ach in streak_achievements[:5]:
            ach_info = achievement_service.get_achievement_info(ach.achievement_type, lang)
            text += f"{ach_info['emoji']} {ach_info['name']}\n"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_comparison_keyboard(lang)
    )


@require_registration
async def cb_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export user data"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    data = query.data.split("_")
    format_type = data[1]  # csv or json
    period = data[2] if len(data) > 2 else "all"
    
    # Get period for export
    if period == "all":
        content, filename = await export_user_data(user_id, format_type)
    else:
        # For specific period, we need to filter
        period_data = await get_period_data(user_id, period)
        # Convert to export format
        if format_type == "csv":
            # Generate CSV for period
            from db import get_logs_for_period
            logs = await get_logs_for_period(
                user_id,
                period_data["start_date"],
                period_data["end_date"]
            )
            content = export_logs_to_csv(logs)
            filename = f"water_export_{period}_{user_id}_{date.today().isoformat()}.csv"
        else:
            # Generate JSON for period
            data = await get_period_export(user_id, period_data)
            import json
            content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            filename = f"water_export_{period}_{user_id}_{date.today().isoformat()}.json"
    
    # Send file
    from io import BytesIO
    file_bytes = BytesIO(content.encode('utf-8'))
    
    await context.bot.send_document(
        chat_id=user_id,
        document=file_bytes,
        filename=filename,
        caption=L["export_success"]
    )
    
    await query.edit_message_text(
        L["export_success"],
        reply_markup=get_stats_keyboard(lang)
    )


async def export_user_data(user_id: int, format_type: str) -> tuple:
    """Export all user data"""
    if format_type == "csv":
        content = await export_to_csv(user_id)
        filename = f"water_export_all_{user_id}_{date.today().isoformat()}.csv"
    else:
        data = await export_to_dict(user_id)
        import json
        content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        filename = f"water_export_all_{user_id}_{date.today().isoformat()}.json"
    
    return content, filename


def export_logs_to_csv(logs) -> str:
    """Convert logs to CSV string"""
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["date", "time", "volume_ml", "effective_ml", "drink_type"])
    
    for log in logs:
        writer.writerow([
            log.logged_date.isoformat(),
            log.logged_at.strftime("%H:%M") if log.logged_at else "",
            log.volume_ml,
            log.effective_ml,
            str(log.drink_type)
        ])
    
    return output.getvalue()


async def get_period_export(user_id: int, period_data: dict) -> dict:
    """Get export data for specific period"""
    from db import get_logs_for_period, get_user
    
    user = await get_user(user_id)
    logs = await get_logs_for_period(
        user_id,
        period_data["start_date"],
        period_data["end_date"]
    )
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
        },
        "period": {
            "start": period_data["start_date"].isoformat(),
            "end": period_data["end_date"].isoformat(),
            "total_ml": period_data["total_ml"],
            "average_ml": period_data["average_ml"],
        },
        "logs": [
            {
                "date": log.logged_date.isoformat(),
                "time": log.logged_at.strftime("%H:%M") if log.logged_at else "",
                "volume_ml": log.volume_ml,
                "effective_ml": log.effective_ml,
                "drink_type": str(log.drink_type),
            }
            for log in logs
        ]
    }


def get_progress_bar(current: int, goal: int, width: int = 10) -> str:
    """Generate progress bar"""
    if goal <= 0:
        return "░" * width
    
    percent = min(current / goal, 1.0)
    filled = int(percent * width)
    
    if percent >= 1.0:
        return "█" * width
    else:
        return "█" * filled + "░" * (width - filled)