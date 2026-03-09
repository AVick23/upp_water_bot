"""
Utility functions for statistics module
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from collections import defaultdict
import calendar

from db import (
    get_logs_for_period, get_date_total, get_user,
    get_user_stats as get_stats
)
from stats.constants import (
    PERIODS, HEATMAP_LEVELS, TIME_SLOTS,
    CHART_SYMBOLS, COMPARISON_MESSAGES, PROGRESS_MESSAGES
)


async def get_user_lang(user_id: int) -> str:
    """Get user's language preference"""
    user = await get_user(user_id)
    return user.language if user else "ru"


async def get_period_data(
    user_id: int,
    period: str,
    target_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Get statistics for a specific period
    """
    if target_date is None:
        target_date = date.today()
    
    period_info = PERIODS.get(period, PERIODS["week"])
    days = period_info.get("days")
    
    if days is None:  # All time
        start_date = date(2000, 1, 1)  # Far past
        end_date = date.today()
    else:
        end_date = target_date
        start_date = target_date - timedelta(days=days - 1)
    
    # Get logs for period
    logs = await get_logs_for_period(user_id, start_date, end_date)
    
    # Group by date
    daily_totals = defaultdict(int)
    for log in logs:
        daily_totals[log.logged_date] += log.effective_ml
    
    # Calculate statistics
    total_ml = sum(daily_totals.values())
    active_days = len(daily_totals)
    avg_per_day = total_ml / days if days and days > 0 else total_ml / max(active_days, 1)
    
    # Find best day
    best_day = None
    best_value = 0
    for d, v in daily_totals.items():
        if v > best_value:
            best_value = v
            best_day = d
    
    return {
        "period": period,
        "period_name": period_info[f"name_{await get_user_lang(user_id)}"],
        "start_date": start_date,
        "end_date": end_date,
        "total_ml": total_ml,
        "active_days": active_days,
        "total_days": days if days else active_days,
        "average_ml": round(avg_per_day),
        "best_day": best_day,
        "best_value": best_value,
        "daily_totals": dict(daily_totals),
    }


def format_heatmap(daily_data: Dict[date, int], goal: int, width: int = 7) -> str:
    """
    Format data as a heatmap (calendar view)
    Returns a string with colored squares
    """
    if not daily_data:
        return "📊 Нет данных за этот период"
    
    # Get first and last dates
    dates = sorted(daily_data.keys())
    if not dates:
        return ""
    
    first_date = dates[0]
    last_date = dates[-1]
    
    # Create calendar grid
    calendar_lines = []
    
    # Month headers
    current_month = None
    month_positions = []
    
    current_date = first_date
    while current_date <= last_date:
        if current_date.month != current_month:
            current_month = current_date.month
            month_name = calendar.month_name[current_month][:3]
            month_positions.append((len(calendar_lines), month_name))
        calendar_lines.append("")
        current_date += timedelta(days=1)
    
    # Fill with data
    result = []
    current_date = first_date
    week = []
    
    # Add weekday headers (simplified - can't use await here)
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    result.append("   " + " ".join(weekdays))
    
    # Add leading spaces for first week
    first_weekday = first_date.weekday()
    week = ["  "] * first_weekday
    
    while current_date <= last_date:
        percent = (daily_data.get(current_date, 0) / goal) * 100 if goal > 0 else 0
        
        # Determine heat level
        symbol = "⬜"  # Default empty
        for level in HEATMAP_LEVELS:
            if level["min"] <= percent <= level["max"]:
                symbol = level["symbol"]
                break
        
        week.append(symbol)
        
        if len(week) == 7:
            week_str = " ".join(week)
            result.append(week_str)
            week = []
        
        current_date += timedelta(days=1)
    
    # Add remaining days
    if week:
        while len(week) < 7:
            week.append("  ")
        week_str = " ".join(week)
        result.append(week_str)
    
    return "\n".join(result)


def format_progress_bar(current: int, goal: int, width: int = 10) -> str:
    """Generate text-based progress bar"""
    if goal <= 0:
        return CHART_SYMBOLS["bar_empty"] * width
    
    percent = min(current / goal, 1.0)
    filled = int(percent * width)
    
    if percent >= 1.0:
        return CHART_SYMBOLS["bar_filled"] * width
    else:
        return CHART_SYMBOLS["bar_filled"] * filled + CHART_SYMBOLS["bar_empty"] * (width - filled)


def calculate_trend(data: List[int]) -> str:
    """Calculate trend direction"""
    if len(data) < 2:
        return CHART_SYMBOLS["trend_flat"]
    
    first_half = sum(data[:len(data)//2]) / (len(data)//2)
    second_half = sum(data[len(data)//2:]) / (len(data) - len(data)//2)
    
    if second_half > first_half * 1.1:
        return CHART_SYMBOLS["trend_up"]
    elif second_half < first_half * 0.9:
        return CHART_SYMBOLS["trend_down"]
    else:
        return CHART_SYMBOLS["trend_flat"]


async def get_time_distribution(user_id: int, days: int = 30) -> Dict[str, int]:
    """
    Get distribution of drinks by time of day
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    logs = await get_logs_for_period(user_id, start_date, end_date)
    
    distribution = {
        "morning": 0,    # 6-12
        "afternoon": 0,  # 12-18
        "evening": 0,    # 18-24
        "night": 0,      # 0-6
    }
    
    for log in logs:
        if log.logged_at:
            hour = log.logged_at.hour
            
            if 6 <= hour < 12:
                distribution["morning"] += log.effective_ml
            elif 12 <= hour < 18:
                distribution["afternoon"] += log.effective_ml
            elif 18 <= hour < 24:
                distribution["evening"] += log.effective_ml
            else:
                distribution["night"] += log.effective_ml
    
    return distribution


def format_time_distribution(distribution: Dict[str, int], lang: str = "ru") -> str:
    """Format time distribution for display"""
    total = sum(distribution.values())
    if total == 0:
        return "📊 Нет данных" if lang == "ru" else "📊 No data"
    
    lines = ["⏰ **Распределение по времени:**" if lang == "ru" else "⏰ **Time distribution:**"]
    
    slots = [
        ("morning", "🌅 Утро" if lang == "ru" else "🌅 Morning"),
        ("afternoon", "☀️ День" if lang == "ru" else "☀️ Afternoon"),
        ("evening", "🌆 Вечер" if lang == "ru" else "🌆 Evening"),
        ("night", "🌙 Ночь" if lang == "ru" else "🌙 Night"),
    ]
    
    for key, name in slots:
        value = distribution.get(key, 0)
        percent = (value / total) * 100
        bar = format_progress_bar(int(value), int(total), 5)
        lines.append(f"{name}: {bar} {percent:.0f}% ({value} мл)")
    
    return "\n".join(lines)


async def get_weekday_distribution(user_id: int, weeks: int = 8) -> Dict[int, int]:
    """
    Get distribution by weekday (0=Monday, 6=Sunday)
    """
    end_date = date.today()
    start_date = end_date - timedelta(weeks=weeks)
    
    logs = await get_logs_for_period(user_id, start_date, end_date)
    
    distribution = defaultdict(int)
    counts = defaultdict(int)
    
    for log in logs:
        weekday = log.logged_date.weekday()
        distribution[weekday] += log.effective_ml
        counts[weekday] += 1
    
    # Calculate averages
    averages = {}
    for day in range(7):
        if counts[day] > 0:
            averages[day] = distribution[day] // counts[day]
        else:
            averages[day] = 0
    
    return averages


def format_weekday_distribution(distribution: Dict[int, int], lang: str = "ru") -> str:
    """Format weekday distribution for display"""
    weekdays = [
        ("Пн", "Mo"), ("Вт", "Tu"), ("Ср", "We"),
        ("Чт", "Th"), ("Пт", "Fr"), ("Сб", "Sa"), ("Вс", "Su")
    ]
    
    lines = ["📆 **По дням недели (среднее):**" if lang == "ru" else "📆 **By weekday (average):**"]
    
    max_value = max(distribution.values()) if distribution else 1
    
    for i, (ru, en) in enumerate(weekdays):
        value = distribution.get(i, 0)
        bar_length = int((value / max_value) * 10) if max_value > 0 else 0
        bar = CHART_SYMBOLS["bar_filled"] * bar_length + CHART_SYMBOLS["bar_empty"] * (10 - bar_length)
        
        day_name = ru if lang == "ru" else en
        lines.append(f"{day_name}: {bar} {value} мл")
    
    return "\n".join(lines)


async def compare_periods(
    user_id: int,
    period1: str,
    period2: str
) -> Dict[str, Any]:
    """
    Compare two periods
    """
    data1 = await get_period_data(user_id, period1)
    data2 = await get_period_data(user_id, period2)
    
    total_change = data2["total_ml"] - data1["total_ml"]
    percent_change = (total_change / data1["total_ml"] * 100) if data1["total_ml"] > 0 else 0
    
    avg_change = data2["average_ml"] - data1["average_ml"]
    avg_percent = (avg_change / data1["average_ml"] * 100) if data1["average_ml"] > 0 else 0
    
    return {
        "period1": data1,
        "period2": data2,
        "total_change": total_change,
        "percent_change": percent_change,
        "avg_change": avg_change,
        "avg_percent": avg_percent,
        "is_better": total_change > 0
    }