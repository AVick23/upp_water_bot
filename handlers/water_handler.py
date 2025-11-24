# handlers/water_handler.py
from telegram import Update
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager  # ← Импортируем класс


async def handle_water_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Убирает "часики" на кнопке

    user_id = query.from_user.id
    db = DatabaseManager()  # ← Создаём экземпляр
    db.add_water_record(user_id, ml=250)  # ← Метод класса
    total_today = db.get_water_today(user_id)  # ← Метод класса

    await query.edit_message_text(
        f"✅ Засчитано! +250 мл\nВсего сегодня: {total_today} мл"
    )