# config/settings.py
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not BOT_TOKEN:
    raise ValueError("Токен бота не найден. Проверьте файл .env")

if not OPENWEATHER_API_KEY:
    raise ValueError("API-ключ OpenWeatherMap не найден. Проверьте файл .env")