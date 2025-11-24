# services/weather_service.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not API_KEY:
    raise ValueError("OPENWEATHER_API_KEY не найден в .env")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_current_temp(city: str) -> float | None:
    """
    Возвращает текущую температуру в °C по названию города.
    Возвращает None, если город не найден или API недоступен.
    """
    if not city:
        return None

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"  # Получаем температуру в Цельсиях
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        return round(data["main"]["temp"], 1)
    except (requests.RequestException, KeyError, ValueError) as e:
        # Логирование ошибки можно добавить позже
        return None