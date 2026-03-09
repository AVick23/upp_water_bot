"""
Utility functions for achievements module
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
from collections import defaultdict

from config import AchievementType, ACHIEVEMENTS, RARITY_COLORS
from db import get_user, get_user_achievements, get_today_total
from achievements.constants import PROGRESS_THRESHOLDS, RARITY_DISPLAY, ACHIEVEMENT_CATEGORIES, UNLOCK_MESSAGES


async def get_user_achievements_data(user_id: int) -> Dict[str, Any]:
    """
    Get comprehensive achievements data for user
    """
    user = await get_user(user_id)
    earned_achievements = await get_user_achievements(user_id)
    
    # Group by category
    by_category = defaultdict(list)
    by_rarity = defaultdict(list)
    earned_ids = []
    
    for ach in earned_achievements:
        ach_type = ach.achievement_type
        earned_ids.append(ach_type.value)
        
        # Find category
        for cat_id, category in ACHIEVEMENT_CATEGORIES.items():
            if ach_type in category["types"]:
                by_category[cat_id].append(ach_type)
                break
        
        # Get rarity
        rarity = ACHIEVEMENTS.get(ach_type, {}).get("rarity", "common")
        by_rarity[rarity].append(ach_type)
    
    # Calculate totals
    total_possible = len(ACHIEVEMENTS)
    total_earned = len(earned_achievements)
    completion_percent = (total_earned / total_possible * 100) if total_possible > 0 else 0
    
    # Calculate XP totals
    total_xp = user.xp if user else 0
    
    return {
        "user_id": user_id,
        "total_earned": total_earned,
        "total_possible": total_possible,
        "completion_percent": round(completion_percent, 1),
        "earned_ids": earned_ids,
        "by_category": dict(by_category),
        "by_rarity": dict(by_rarity),
        "total_xp": total_xp,
        "level": user.level if user else 1,
    }


async def get_achievement_progress(
    user_id: int,
    ach_type: AchievementType
) -> Dict[str, Any]:
    """
    Get progress towards a specific achievement
    """
    user = await get_user(user_id)
    if not user:
        return {"progress": 0, "target": 0, "percent": 0}
    
    # Get threshold from constants
    target = PROGRESS_THRESHOLDS.get(ach_type, 0)
    
    if target == 0:
        # For non-numeric achievements, just return earned status
        from db import has_achievement
        earned = await has_achievement(user_id, ach_type)
        return {
            "progress": 1 if earned else 0,
            "target": 1,
            "percent": 100 if earned else 0,
            "earned": earned
        }
    
    # Calculate progress based on achievement type
    progress = 0
    
    if "streak" in ach_type.value:
        # Streak achievements
        progress = user.current_streak or 0
    
    elif "volume" in ach_type.value:
        # Volume achievements
        progress = user.total_water_ml or 0
    
    elif ach_type == AchievementType.EARLY_BIRD:
        # Check if ever achieved
        from db import has_achievement
        earned = await has_achievement(user_id, ach_type)
        progress = 1 if earned else 0
        target = 1
    
    elif ach_type == AchievementType.MORNING_HYDRATION:
        # Morning hydration - need 500ml before 10am
        today_total = await get_today_total(user_id)
        hour = datetime.now().hour
        if hour < 10:
            progress = min(today_total, 500)
        else:
            # Check if ever achieved
            from db import has_achievement
            earned = await has_achievement(user_id, ach_type)
            progress = 1 if earned else 0
            target = 1
    
    # Calculate percentage
    percent = (progress / target * 100) if target > 0 else 0
    
    return {
        "progress": progress,
        "target": target,
        "percent": min(round(percent, 1), 100),
        "remaining": max(0, target - progress),
        "earned": progress >= target
    }


async def get_next_achievements(user_id: int, limit: int = 5) -> List[Dict]:
    """
    Get next achievable achievements (closest to completion)
    """
    user = await get_user(user_id)
    if not user:
        return []
    
    from db import has_achievement
    
    next_achievements = []
    
    for ach_type, target in PROGRESS_THRESHOLDS.items():
        # Skip if already earned
        if await has_achievement(user_id, ach_type):
            continue
        
        # Calculate progress
        if "streak" in ach_type.value:
            progress = user.current_streak or 0
        elif "volume" in ach_type.value:
            progress = user.total_water_ml or 0
        else:
            continue
        
        if progress > 0:
            percent = (progress / target * 100)
            remaining = target - progress
            
            next_achievements.append({
                "type": ach_type,
                "progress": progress,
                "target": target,
                "percent": round(percent, 1),
                "remaining": remaining,
                "info": ACHIEVEMENTS.get(ach_type, {})
            })
    
    # Sort by percent (closest to completion first)
    next_achievements.sort(key=lambda x: x["percent"], reverse=True)
    
    return next_achievements[:limit]


def format_achievement_text(
    ach_type: AchievementType,
    earned: bool,
    progress: Optional[Dict] = None,
    lang: str = "ru"
) -> str:
    """
    Format achievement display text
    """
    from config import Locale
    
    info = ACHIEVEMENTS.get(ach_type, {})
    name_key = f"ach_{ach_type.value}"
    name = Locale.get(name_key, lang)
    
    description_key = f"ach_{ach_type.value}_desc"
    description = Locale.get(description_key, lang)
    if description == description_key:  # No description
        description = ""
    
    rarity = info.get("rarity", "common")
    rarity_info = RARITY_DISPLAY.get(rarity, {})
    rarity_name = rarity_info.get(f"name_{lang}", rarity)
    rarity_emoji = rarity_info.get("emoji", "⚪")
    
    xp = info.get("xp", 0)
    emoji = info.get("emoji", "🏆")
    
    # Build text
    if earned:
        status = "✅ **" + ("ПОЛУЧЕНО", "EARNED")[lang == "en"] + "**"
    else:
        status = "❌ **" + ("НЕ ПОЛУЧЕНО", "NOT EARNED")[lang == "en"] + "**"
    
    text = [
        f"{emoji} **{name}**",
        f"{rarity_emoji} {rarity_name} • +{xp} XP",
        f"_{description}_" if description else "",
        "",
        status,
    ]
    
    # Add progress if available
    if progress and not earned:
        bar = get_progress_bar(progress["progress"], progress["target"], 10)
        text.extend([
            "",
            f"{bar}",
            f"{progress['progress']} / {progress['target']} ({progress['percent']}%)",
        ])
    
    return "\n".join(text)


def format_achievement_unlock(
    ach_type: AchievementType,
    lang: str = "ru"
) -> str:
    """
    Format achievement unlock notification
    """
    from config import Locale
    
    info = ACHIEVEMENTS.get(ach_type, {})
    name_key = f"ach_{ach_type.value}"
    name = Locale.get(name_key, lang)
    
    rarity = info.get("rarity", "common")
    xp = info.get("xp", 0)
    emoji = info.get("emoji", "🏆")
    
    messages = UNLOCK_MESSAGES["ru"] if lang == "ru" else UNLOCK_MESSAGES["en"]
    
    # Different formatting based on rarity
    if rarity == "mythic":
        return (
            f"💎✨ **{messages['title']}** ✨💎\n\n"
            f"{emoji} **{name}**\n"
            f"🔴 +{xp} XP\n\n"
            f"_{messages['congrats']}_ 🎉"
        )
    elif rarity == "legendary":
        return (
            f"🌟 **{messages['title']}** 🌟\n\n"
            f"{emoji} **{name}**\n"
            f"🟡 +{xp} XP\n\n"
            f"_{messages['congrats']}_ 🎉"
        )
    else:
        rarity_emoji = RARITY_DISPLAY.get(rarity, {}).get("emoji", "⚪")
        return (
            f"{rarity_emoji} **{messages['new']}**\n\n"
            f"{emoji} **{name}**\n"
            f"+{xp} XP"
        )


def get_progress_bar(current: int, target: int, width: int = 10) -> str:
    """Generate progress bar for achievements"""
    if target <= 0:
        return "░" * width
    
    percent = min(current / target, 1.0)
    filled = int(percent * width)
    
    if percent >= 1.0:
        return "█" * width
    else:
        return "█" * filled + "░" * (width - filled)


def get_rarity_stats(earned_by_rarity: Dict[str, List]) -> Dict[str, Any]:
    """
    Get statistics by rarity
    """
    stats = {}
    
    for rarity, display in RARITY_DISPLAY.items():
        total = len([a for a in ACHIEVEMENTS.values() if a.get("rarity") == rarity])
        earned = len(earned_by_rarity.get(rarity, []))
        
        stats[rarity] = {
            "name_ru": display["name_ru"],
            "name_en": display["name_en"],
            "emoji": display["emoji"],
            "total": total,
            "earned": earned,
            "percent": round((earned / total * 100) if total > 0 else 0, 1)
        }
    
    return stats


def get_recent_achievements(
    achievements: List,
    days: int = 30,
    limit: int = 5
) -> List[Dict]:
    """
    Get recent achievements (last N days)
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = []
    
    for ach in achievements:
        if ach.earned_at and ach.earned_at > cutoff:
            recent.append({
                "type": ach.achievement_type,
                "earned_at": ach.earned_at,
                "info": ACHIEVEMENTS.get(ach.achievement_type, {})
            })
    
    # Sort by date (newest first)
    recent.sort(key=lambda x: x["earned_at"], reverse=True)
    
    return recent[:limit]


def check_achievement_completion(ach_type: AchievementType, value: int) -> bool:
    """
    Check if a numeric achievement is completed
    """
    target = PROGRESS_THRESHOLDS.get(ach_type)
    if target:
        return value >= target
    return False


def get_achievement_difficulty(rarity: str) -> str:
    """
    Get difficulty description based on rarity
    """
    difficulties = {
        "common": "⭐" * 1,
        "uncommon": "⭐" * 2,
        "rare": "⭐⭐⭐",
        "epic": "⭐⭐⭐⭐",
        "legendary": "⭐⭐⭐⭐⭐",
        "mythic": "🔥🔥🔥🔥🔥",
    }
    return difficulties.get(rarity, "⭐")