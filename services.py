"""
Business Logic Services for WaterBot
Water calculation, weather, achievements, insights
"""

import asyncio
import aiohttp
import math
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from config import (
    Gender, ActivityLevel, ActivityMode, DrinkType, AchievementType,
    DRINK_COEFFICIENTS, ACHIEVEMENTS, config, Locale
)
from database import (
    get_user, update_user, get_today_total, get_date_total,
    add_achievement, has_achievement, update_streak, check_streak_lost,
    get_week_stats, get_month_heatmap, add_insight, export_to_dict, export_to_csv,
    get_logs_for_period
)


# ============================================================================
# WATER NORM CALCULATION
# ============================================================================

@dataclass
class WaterNormResult:
    """Result of water norm calculation"""
    base_norm: int  # ml
    weather_adjusted: int  # ml after weather correction
    mode_adjusted: int  # ml after mode correction
    final_norm: int  # final daily goal
    weather_bonus_percent: int
    mode_name: str


def calculate_water_norm(
    weight: float,
    gender: Gender = Gender.MALE,
    activity_level: ActivityLevel = ActivityLevel.MEDIUM,
    temperature_celsius: float = 20.0,
    activity_mode: ActivityMode = ActivityMode.NORMAL
) -> WaterNormResult:
    """
    Calculate daily water norm based on:
    Base formula: weight × 30 ml × K_gender × K_activity × K_weather
    
    K_gender: 1.1 for male, 1.0 for female
    K_activity: 1.0 low, 1.1 medium, 1.2 high
    K_weather: +5% per 5°C above 20°C (max +30%)
    """
    
    # Base calculation
    base_ml = weight * 30
    
    # Gender coefficient
    gender_k = 1.1 if gender == Gender.MALE else 1.0
    base_ml *= gender_k
    
    # Activity coefficient
    activity_k = {
        ActivityLevel.LOW: 1.0,
        ActivityLevel.MEDIUM: 1.1,
        ActivityLevel.HIGH: 1.2
    }.get(activity_level, 1.1)
    base_ml *= activity_k
    
    base_norm = int(base_ml)
    
    # Weather adjustment (+5% per 5°C above 20°C)
    weather_bonus = 0
    if temperature_celsius > 20:
        degrees_over = temperature_celsius - 20
        weather_bonus = min(int(degrees_over / 5) * 5, 30)  # Max 30%
    
    weather_adjusted = int(base_norm * (1 + weather_bonus / 100))
    
    # Activity mode adjustment
    mode_k = {
        ActivityMode.NORMAL: 1.0,
        ActivityMode.WORKOUT: 1.3,  # +30%
        ActivityMode.FOCUS: 1.0,
        ActivityMode.VACATION: 0.8  # -20%
    }.get(activity_mode, 1.0)
    
    mode_adjusted = int(weather_adjusted * mode_k)
    
    # Clamp to reasonable limits
    final_norm = max(config.MIN_DAILY_WATER_ML, min(mode_adjusted, config.MAX_DAILY_WATER_ML))
    
    mode_names = {
        ActivityMode.NORMAL: "normal",
        ActivityMode.WORKOUT: "workout",
        ActivityMode.FOCUS: "focus",
        ActivityMode.VACATION: "vacation"
    }
    
    return WaterNormResult(
        base_norm=base_norm,
        weather_adjusted=weather_adjusted,
        mode_adjusted=mode_adjusted,
        final_norm=final_norm,
        weather_bonus_percent=weather_bonus,
        mode_name=mode_names.get(activity_mode, "normal")
    )


def get_user_daily_norm(user_id: int, temperature: float = 20.0) -> int:
    """Get calculated daily norm for a user"""
    user = get_user(user_id)
    if not user or not user.weight:
        return 2000  # Default
    
    result = calculate_water_norm(
        weight=user.weight,
        gender=user.gender or Gender.MALE,
        activity_level=user.activity_level or ActivityLevel.MEDIUM,
        temperature_celsius=temperature,
        activity_mode=user.activity_mode or ActivityMode.NORMAL
    )
    
    return result.final_norm


# ============================================================================
# WEATHER SERVICE
# ============================================================================

@dataclass
class WeatherData:
    """Weather data for a location"""
    temperature: float
    feels_like: float
    humidity: int
    description: str
    icon: str
    city: str


class WeatherService:
    """OpenWeatherMap API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self._cache: Dict[str, Tuple[WeatherData, datetime]] = {}
        self._cache_ttl = timedelta(hours=1)
    
    async def get_weather(self, city: str) -> Optional[WeatherData]:
        """Get current weather for a city"""
        if not self.api_key:
            return None
        
        # Check cache
        cache_key = city.lower()
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                return data
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "q": city,
                    "appid": self.api_key,
                    "units": "metric",
                    "lang": "ru"
                }
                async with session.get(self.base_url, params=params) as resp:
                    if resp.status != 200:
                        return None
                    
                    data = await resp.json()
                    
                    weather = WeatherData(
                        temperature=data["main"]["temp"],
                        feels_like=data["main"]["feels_like"],
                        humidity=data["main"]["humidity"],
                        description=data["weather"][0]["description"],
                        icon=data["weather"][0]["icon"],
                        city=data["name"]
                    )
                    
                    # Cache result
                    self._cache[cache_key] = (weather, datetime.utcnow())
                    return weather
                    
        except Exception as e:
            print(f"Weather API error: {e}")
            return None
    
    def get_weather_emoji(self, icon_code: str) -> str:
        """Convert OpenWeatherMap icon code to emoji"""
        emoji_map = {
            "01": "☀️",  # clear
            "02": "⛅",  # few clouds
            "03": "☁️",  # scattered clouds
            "04": "☁️",  # broken clouds
            "09": "🌧️",  # shower rain
            "10": "🌧️",  # rain
            "11": "⛈️",  # thunderstorm
            "13": "❄️",  # snow
            "50": "🌫️",  # mist
        }
        return emoji_map.get(icon_code[:2], "🌡️")


weather_service = WeatherService()


# ============================================================================
# ACHIEVEMENTS SERVICE
# ============================================================================

class AchievementService:
    """Service for checking and awarding achievements"""
    
    @staticmethod
    async def check_all_achievements(user_id: int, volume_ml: int = None, drink_type: DrinkType = None) -> List[AchievementType]:
        """Check all possible achievements for a user"""
        new_achievements = []
        
        user = get_user(user_id)
        if not user:
            return new_achievements
        
        # Streak achievements
        streak = user.current_streak or 0
        new_achievements.extend(
            AchievementService._check_streak_achievements(user_id, streak)
        )
        
        # Volume achievements
        total = user.total_water_ml or 0
        if volume_ml:
            total += volume_ml
        new_achievements.extend(
            AchievementService._check_volume_achievements(user_id, total)
        )
        
        # Time-based achievements
        new_achievements.extend(
            AchievementService._check_time_achievements(user_id, volume_ml)
        )
        
        # Overachievement (выполнение/превышение нормы)
        new_achievements.extend(
            AchievementService._check_overachievement(user_id)
        )
        
        # Drink type achievements
        new_achievements.extend(
            AchievementService._check_drink_achievements(user_id, drink_type)
        )
        
        # Week day achievements
        new_achievements.extend(
            AchievementService._check_weekday_achievements(user_id)
        )
        
        # Seasonal achievements
        new_achievements.extend(
            AchievementService._check_seasonal_achievements(user_id)
        )
        
        # Special achievements (first day, comeback, etc.)
        new_achievements.extend(
            AchievementService._check_special_achievements(user_id)
        )
        
        return new_achievements
    
    @staticmethod
    def _check_streak_achievements(user_id: int, streak: int) -> List[AchievementType]:
        """Check streak-based achievements"""
        achievements = []
        
        streak_thresholds = [
            (3, AchievementType.STREAK_3),
            (7, AchievementType.STREAK_7),
            (14, AchievementType.STREAK_14),
            (21, AchievementType.STREAK_21),
            (30, AchievementType.STREAK_30),
            (50, AchievementType.STREAK_50),
            (100, AchievementType.STREAK_100),
            (200, AchievementType.STREAK_200),
            (365, AchievementType.STREAK_365),
            (500, AchievementType.STREAK_500),
            (1000, AchievementType.STREAK_1000),
        ]
        
        for threshold, ach_type in streak_thresholds:
            if streak >= threshold and not has_achievement(user_id, ach_type):
                add_achievement(user_id, ach_type, {"streak": streak})
                achievements.append(ach_type)
        
        return achievements
    
    @staticmethod
    def _check_volume_achievements(user_id: int, total_ml: int) -> List[AchievementType]:
        """Check total volume achievements"""
        achievements = []
        
        volume_thresholds = [
            (5000, AchievementType.VOLUME_5L),
            (10000, AchievementType.VOLUME_10L),
            (25000, AchievementType.VOLUME_25L),
            (50000, AchievementType.VOLUME_50L),
            (100000, AchievementType.VOLUME_100L),
            (250000, AchievementType.VOLUME_250L),
            (500000, AchievementType.VOLUME_500L),
            (1000000, AchievementType.VOLUME_1000L),
            (2500000, AchievementType.VOLUME_2500L),
            (5000000, AchievementType.VOLUME_5000L),
            (10000000, AchievementType.VOLUME_10000L),
        ]
        
        for threshold, ach_type in volume_thresholds:
            if total_ml >= threshold and not has_achievement(user_id, ach_type):
                add_achievement(user_id, ach_type, {"total_ml": total_ml})
                achievements.append(ach_type)
        
        return achievements
    
    @staticmethod
    def _check_time_achievements(user_id: int, volume_ml: int) -> List[AchievementType]:
        """Check time-based achievements"""
        achievements = []
        now = datetime.now()
        
        if not volume_ml:
            return achievements
        
        # Early bird - drink before 8 AM
        if now.hour < 8:
            if not has_achievement(user_id, AchievementType.EARLY_BIRD):
                add_achievement(user_id, AchievementType.EARLY_BIRD, {"time": now.isoformat()})
                achievements.append(AchievementType.EARLY_BIRD)
        
        # Morning hydration - drink 500ml before 10 AM
        if now.hour < 10:
            today_total = get_today_total(user_id)
            if today_total >= 500:
                if not has_achievement(user_id, AchievementType.MORNING_HYDRATION):
                    add_achievement(user_id, AchievementType.MORNING_HYDRATION, {"volume": today_total})
                    achievements.append(AchievementType.MORNING_HYDRATION)
        
        # Lunch break - drink between 12 and 14
        if 12 <= now.hour < 14:
            if not has_achievement(user_id, AchievementType.LUNCH_BREAK):
                add_achievement(user_id, AchievementType.LUNCH_BREAK, {"time": now.isoformat()})
                achievements.append(AchievementType.LUNCH_BREAK)
        
        # Evening calm - drink between 18 and 21
        if 18 <= now.hour < 21:
            if not has_achievement(user_id, AchievementType.EVENING_CALM):
                add_achievement(user_id, AchievementType.EVENING_CALM, {"time": now.isoformat()})
                achievements.append(AchievementType.EVENING_CALM)
        
        # Night owl - drink after 23:00
        if now.hour >= 23:
            if not has_achievement(user_id, AchievementType.NIGHT_OWL):
                add_achievement(user_id, AchievementType.NIGHT_OWL, {"time": now.isoformat()})
                achievements.append(AchievementType.NIGHT_OWL)
        
        # Midnight snack - drink between 00:00 and 05:00
        if 0 <= now.hour < 5:
            if not has_achievement(user_id, AchievementType.MIDNIGHT_SNACK):
                add_achievement(user_id, AchievementType.MIDNIGHT_SNACK, {"time": now.isoformat()})
                achievements.append(AchievementType.MIDNIGHT_SNACK)
        
        return achievements
    
    @staticmethod
    def _check_overachievement(user_id: int) -> List[AchievementType]:
        """Check overachievement achievements"""
        achievements = []
        today_total = get_today_total(user_id)
        goal = get_user_daily_norm(user_id)
        
        if goal <= 0:
            return achievements
        
        percent = (today_total / goal) * 100
        
        # Exact norm - within 50ml tolerance
        if abs(today_total - goal) <= 50:
            if not has_achievement(user_id, AchievementType.EXACT_NORM):
                add_achievement(user_id, AchievementType.EXACT_NORM, {"ml": today_total})
                achievements.append(AchievementType.EXACT_NORM)
        
        # Over 110%
        if percent >= 110:
            if not has_achievement(user_id, AchievementType.OVER_110):
                add_achievement(user_id, AchievementType.OVER_110, {"percent": percent})
                achievements.append(AchievementType.OVER_110)
        
        # Over 125%
        if percent >= 125:
            if not has_achievement(user_id, AchievementType.OVER_125):
                add_achievement(user_id, AchievementType.OVER_125, {"percent": percent})
                achievements.append(AchievementType.OVER_125)
        
        # Over 150%
        if percent >= 150:
            if not has_achievement(user_id, AchievementType.OVER_150):
                add_achievement(user_id, AchievementType.OVER_150, {"percent": percent})
                achievements.append(AchievementType.OVER_150)
        
        # Over 200%
        if percent >= 200:
            if not has_achievement(user_id, AchievementType.OVER_200):
                add_achievement(user_id, AchievementType.OVER_200, {"percent": percent})
                achievements.append(AchievementType.OVER_200)
        
        return achievements
    
    @staticmethod
    def _check_drink_achievements(user_id: int, drink_type: DrinkType) -> List[AchievementType]:
        """Check drink type achievements"""
        achievements = []
        from database import get_drink_breakdown, get_logs_for_period
        
        # Check variety king - all 5 drink types in one day
        breakdown = get_drink_breakdown(user_id)
        if len(breakdown) >= 5:
            if not has_achievement(user_id, AchievementType.VARIETY_KING):
                add_achievement(user_id, AchievementType.VARIETY_KING, {"types": list(breakdown.keys())})
                achievements.append(AchievementType.VARIETY_KING)
        
        return achievements
    
    @staticmethod
    def _check_weekday_achievements(user_id: int) -> List[AchievementType]:
        """Check week day achievements"""
        achievements = []
        now = datetime.now()
        today_total = get_today_total(user_id)
        goal = get_user_daily_norm(user_id)
        
        if today_total < goal:
            return achievements
        
        weekday = now.weekday()
        
        # Monday - day 0
        if weekday == 0:
            if not has_achievement(user_id, AchievementType.MONDAY_START):
                add_achievement(user_id, AchievementType.MONDAY_START, {"date": now.date().isoformat()})
                achievements.append(AchievementType.MONDAY_START)
        
        # Friday - day 4
        if weekday == 4:
            if not has_achievement(user_id, AchievementType.FRIDAY_VIBE):
                add_achievement(user_id, AchievementType.FRIDAY_VIBE, {"date": now.date().isoformat()})
                achievements.append(AchievementType.FRIDAY_VIBE)
        
        # Weekend - days 5, 6
        if weekday >= 5:
            if not has_achievement(user_id, AchievementType.WEEKEND_HERO):
                add_achievement(user_id, AchievementType.WEEKEND_HERO, {"date": now.date().isoformat()})
                achievements.append(AchievementType.WEEKEND_HERO)
        
        return achievements
    
    @staticmethod
    def _check_seasonal_achievements(user_id: int) -> List[AchievementType]:
        """Check seasonal achievements"""
        achievements = []
        now = datetime.now()
        month = now.month
        today_total = get_today_total(user_id)
        goal = get_user_daily_norm(user_id)
        
        if today_total < goal:
            return achievements
        
        # Winter: Dec, Jan, Feb
        if month in [12, 1, 2]:
            if not has_achievement(user_id, AchievementType.WINTER_HYDRATION):
                add_achievement(user_id, AchievementType.WINTER_HYDRATION, {"month": month})
                achievements.append(AchievementType.WINTER_HYDRATION)
        
        # Spring: Mar, Apr, May
        if month in [3, 4, 5]:
            if not has_achievement(user_id, AchievementType.SPRING_AWAKENING):
                add_achievement(user_id, AchievementType.SPRING_AWAKENING, {"month": month})
                achievements.append(AchievementType.SPRING_AWAKENING)
        
        # Summer: Jun, Jul, Aug
        if month in [6, 7, 8]:
            if not has_achievement(user_id, AchievementType.SUMMER_HEAT):
                add_achievement(user_id, AchievementType.SUMMER_HEAT, {"month": month})
                achievements.append(AchievementType.SUMMER_HEAT)
        
        # Autumn: Sep, Oct, Nov
        if month in [9, 10, 11]:
            if not has_achievement(user_id, AchievementType.AUTUMN_RAIN):
                add_achievement(user_id, AchievementType.AUTUMN_RAIN, {"month": month})
                achievements.append(AchievementType.AUTUMN_RAIN)
        
        # New Year - Jan 1st
        if month == 1 and now.day == 1:
            if not has_achievement(user_id, AchievementType.NEW_YEAR):
                add_achievement(user_id, AchievementType.NEW_YEAR, {"year": now.year})
                achievements.append(AchievementType.NEW_YEAR)
        
        return achievements
    
    @staticmethod
    def _check_special_achievements(user_id: int) -> List[AchievementType]:
        """Check special achievements"""
        achievements = []
        user = get_user(user_id)
        
        if not user:
            return achievements
        
        # First day
        if not has_achievement(user_id, AchievementType.FIRST_DAY):
            add_achievement(user_id, AchievementType.FIRST_DAY, {"date": datetime.now().date().isoformat()})
            achievements.append(AchievementType.FIRST_DAY)
        
        # First week - 7 days since registration
        if user.created_at:
            days_since = (datetime.utcnow() - user.created_at).days
            if days_since >= 7 and not has_achievement(user_id, AchievementType.FIRST_WEEK):
                add_achievement(user_id, AchievementType.FIRST_WEEK, {"days": days_since})
                achievements.append(AchievementType.FIRST_WEEK)
            
            if days_since >= 30 and not has_achievement(user_id, AchievementType.FIRST_MONTH):
                add_achievement(user_id, AchievementType.FIRST_MONTH, {"days": days_since})
                achievements.append(AchievementType.FIRST_MONTH)
        
        # Comeback - after 3+ days of inactivity
        if user.last_active_date:
            days_inactive = (date.today() - user.last_active_date).days
            if days_inactive >= 3 and not has_achievement(user_id, AchievementType.COMEBACK):
                add_achievement(user_id, AchievementType.COMEBACK, {"days_inactive": days_inactive})
                achievements.append(AchievementType.COMEBACK)
        
        return achievements
    
    @staticmethod
    def get_achievement_info(ach_type: AchievementType, lang: str = "ru") -> Dict:
        """Get achievement info with localized name"""
        from config import RARITY_COLORS
        
        info = ACHIEVEMENTS.get(ach_type, {})
        name_key = f"ach_{ach_type.value}"
        rarity = info.get("rarity", "common")
        
        return {
            "type": ach_type,
            "emoji": info.get("emoji", "🏆"),
            "name": Locale.get(name_key, lang),
            "xp": info.get("xp", 0),
            "rarity": rarity,
            "rarity_emoji": RARITY_COLORS.get(rarity, "⚪"),
            "rarity_name": Locale.get(f"rarity_{rarity}", lang)
        }

achievement_service = AchievementService()


# ============================================================================
# INSIGHTS SERVICE
# ============================================================================

class InsightsService:
    """Service for generating user insights"""
    
    @staticmethod
    async def generate_weekly_insights(user_id: int, lang: str = "ru") -> List[str]:
        """Generate insights based on weekly patterns"""
        insights = []
        
        week_stats = get_week_stats(user_id)
        if not week_stats.days:
            return insights
        
        # Calculate patterns
        weekday_avg = sum(d.total_ml for d in week_stats.days[:5]) / 5 if week_stats.days[:5] else 0
        weekend_avg = sum(d.total_ml for d in week_stats.days[5:]) / 2 if week_stats.days[5:] else 0
        
        # Weekend vs weekday pattern
        if weekend_avg > 0 and weekday_avg > 0:
            diff_percent = ((weekend_avg - weekday_avg) / weekday_avg) * 100
            
            if diff_percent > 20:
                if lang == "ru":
                    insights.append(f"📊 Вы пьёте на {int(diff_percent)}% больше в выходные!")
                else:
                    insights.append(f"📊 You drink {int(diff_percent)}% more on weekends!")
            elif diff_percent < -20:
                if lang == "ru":
                    insights.append(f"📊 В выходные вы пьёте на {int(abs(diff_percent))}% меньше. Попробуйте поставить напоминания!")
                else:
                    insights.append(f"📊 You drink {int(abs(diff_percent))}% less on weekends. Try setting reminders!")
        
        # Time-based patterns (simplified)
        user = get_user(user_id)
        if user:
            # Check if user has low activity in evening
            evening_logs = 0
            total_logs = 0
            
            logs = get_logs_for_period(user_id, date.today() - timedelta(days=7), date.today())
            for log in logs:
                total_logs += 1
                if log.logged_at and log.logged_at.hour >= 18:
                    evening_logs += 1
            
            if total_logs > 0 and evening_logs / total_logs < 0.15:
                if lang == "ru":
                    insights.append("💡 Вы редко пьёте воду после 18:00. Попробуйте напоминание на 17:30!")
                else:
                    insights.append("💡 You rarely drink water after 6 PM. Try a reminder at 5:30 PM!")
        
        # Best day insight
        if week_stats.best_day and week_stats.best_day.total_ml > 0:
            day_name = week_stats.best_day.date.strftime("%A")
            if lang == "ru":
                day_names = {
                    "Monday": "понедельник", "Tuesday": "вторник",
                    "Wednesday": "среду", "Thursday": "четверг",
                    "Friday": "пятницу", "Saturday": "субботу", "Sunday": "воскресенье"
                }
                day_name = day_names.get(day_name, day_name)
                insights.append(f"🏆 Лучший результат был в {day_name}: {week_stats.best_day.total_ml} мл")
            else:
                insights.append(f"🏆 Best result was on {day_name}: {week_stats.best_day.total_ml} ml")
        
        # Streak insight
        if week_stats.streak >= 3:
            if lang == "ru":
                insights.append(f"🔥 Отличная серия: {week_stats.streak} дней подряд!")
            else:
                insights.append(f"🔥 Great streak: {week_stats.streak} days in a row!")
        
        # Save insights
        for text in insights:
            add_insight(user_id, text, "weekly_pattern")
        
        return insights


insights_service = InsightsService()


# ============================================================================
# MOTIVATION SERVICE
# ============================================================================

class MotivationService:
    """Service for generating motivational messages"""
    
    @staticmethod
    def get_motivation(percent: float, lang: str = "ru") -> str:
        """Get motivational message based on progress percentage"""
        if percent >= 100:
            return Locale.get("motivation_goal_reached", lang)
        elif percent >= 80:
            return Locale.get("motivation_almost", lang)
        elif percent >= 50:
            return Locale.get("motivation_great", lang)
        else:
            return Locale.get("motivation_need_more", lang)
    
    @staticmethod
    def get_time_based_greeting(lang: str = "ru") -> str:
        """Get greeting based on time of day"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "☀️ " + ("Доброе утро!" if lang == "ru" else "Good morning!")
        elif 12 <= hour < 18:
            return "🌤️ " + ("Добрый день!" if lang == "ru" else "Good afternoon!")
        elif 18 <= hour < 22:
            return "🌅 " + ("Добрый вечер!" if lang == "ru" else "Good evening!")
        else:
            return "🌙 " + ("Доброй ночи!" if lang == "ru" else "Good night!")


motivation_service = MotivationService()


# ============================================================================
# PROGRESS VISUALIZATION
# ============================================================================

def get_progress_bar(current: int, goal: int, width: int = 10) -> str:
    """Generate text-based progress bar"""
    if goal <= 0:
        return "░" * width
    
    percent = min(current / goal, 1.0)
    filled = int(percent * width)
    empty = width - filled
    
    # Use different characters for different fill levels
    if percent >= 1.0:
        return "💧" * width
    else:
        return "💧" * filled + "░" * empty


def get_water_glass_emoji(percent: float) -> str:
    """Get glass emoji based on fill level"""
    if percent >= 100:
        return "🥤"
    elif percent >= 75:
        return "🥛"
    elif percent >= 50:
        return "🍵"
    elif percent >= 25:
        return "☕"
    else:
        return "🥄"


def format_main_message(
    current_ml: int,
    goal_ml: int,
    streak: int,
    temperature: float = None,
    weather_desc: str = None,
    lang: str = "ru"
) -> str:
    """Format main menu message"""
    percent = round((current_ml / goal_ml) * 100, 1) if goal_ml > 0 else 0
    glass = get_water_glass_emoji(percent)
    bar = get_progress_bar(current_ml, goal_ml)
    motivation = motivation_service.get_motivation(percent, lang)
    
    lines = [
        f"{glass} **{Locale.get('main_today', lang)}**",
        f"",
        f"`{bar}`",
        f"**{current_ml}** / {goal_ml} мл ({min(percent, 100):.0f}%)",
        f"",
    ]
    
    if streak > 0:
        lines.append(f"🔥 {streak} {Locale.get('stats_days', lang)}")
    
    if temperature is not None:
        weather_line = f"🌡️ {temperature:.0f}°C"
        if weather_desc:
            weather_line += f" • {weather_desc}"
        lines.append(weather_line)
    
    lines.append(f"")
    lines.append(f"_{motivation}_")
    
    return "\n".join(lines)


# ============================================================================
# TIMEZONE HELPERS
# ============================================================================

def get_user_local_time(user_id: int) -> datetime:
    """Get user's local time based on their timezone"""
    from zoneinfo import ZoneInfo
    
    user = get_user(user_id)
    if not user or not user.timezone:
        return datetime.utcnow()
    
    try:
        tz = ZoneInfo(user.timezone)
        return datetime.now(tz)
    except:
        return datetime.utcnow()


def get_user_local_date(user_id: int) -> date:
    """Get user's local date"""
    return get_user_local_time(user_id).date()


# ============================================================================
# DATA EXPORT
# ============================================================================

async def export_user_data(user_id: int, format: str = "json") -> Tuple[str, str]:
    """Export user data in specified format
    
    Returns: (content, filename)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == "csv":
        content = export_to_csv(user_id)
        filename = f"water_export_{user_id}_{timestamp}.csv"
    else:
        import json
        data = export_to_dict(user_id)
        content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        filename = f"water_export_{user_id}_{timestamp}.json"
    
    return content, filename