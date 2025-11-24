# services/weather_service.py
import requests
from config.settings import OPENWEATHER_API_KEY


def get_current_temp(city: str) -> float | None:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return round(data['main']['temp'])
        return None
    except Exception:
        return None


def validate_city(city: str) -> bool:
    """
    Проверяет, существует ли город в OpenWeatherMap API.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(url)
        return response.status_code == 200
    except Exception:
        return False