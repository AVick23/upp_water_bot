# handlers/stats_handler.py
from services.water_calculator import calculate_norm
from services.weather_service import get_current_temp
from database.db_manager import DatabaseManager  # ← Импортируем класс
from telegram import Update
from telegram.ext import ContextTypes


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = DatabaseManager()  # ← Создаём экземпляр
    user = db.get_user(user_id)  # ← Метод класса

    if not user:
        await update.message.reply_text("Сначала пройдите регистрацию через /start.")
        return

    # Получаем температуру
    temperature = None
    if user.get("city"):
        temperature = get_current_temp(user["city"])

    total_ml = db.get_water_today(user_id)  # ← Метод класса
    norm_ml = calculate_norm(user, temperature=temperature)
    glasses_done = total_ml // 250
    glasses_total = norm_ml // 250
    percent = min(100, round(total_ml / norm_ml * 100)) if norm_ml > 0 else 0

    message = (
        f"📊 Статистика за сегодня:\n"
        f"Выпито: {total_ml} мл ({glasses_done} стаканов)\n"
        f"Норма: {norm_ml} мл ({glasses_total} стаканов)\n"
        f"Выполнено: {percent}%"
    )
    if temperature is not None:
        message += f"\n🌡 Температура: {temperature}°C"

    await update.message.reply_text(message)