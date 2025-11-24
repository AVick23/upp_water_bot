# handlers/notifications_handler.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager  # ← Импортируем класс


async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = DatabaseManager()  # ← Создаём экземпляр
    user = db.get_user(user_id)  # ← Метод класса

    if not user:
        await update.message.reply_text("Сначала пройдите регистрацию через /start.")
        return

    status = "включены ✅" if user["notifications_enabled"] else "отключены ❌"
    keyboard = [
        [InlineKeyboardButton("🔔 Включить уведомления", callback_data="notif_enable")],
        [InlineKeyboardButton("🔕 Отключить уведомления", callback_data="notif_disable")]
    ]

    await update.message.reply_text(
        f"Текущий статус уведомлений: {status}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    action = query.data

    db = DatabaseManager()  # ← Создаём экземпляр

    if action == "notif_enable":
        db.update_notifications_enabled(user_id, enabled=True)  # ← Метод класса
        new_status = "включены ✅"
    elif action == "notif_disable":
        db.update_notifications_enabled(user_id, enabled=False)  # ← Метод класса
        new_status = "отключены ❌"
    else:
        return

    await query.edit_message_text(f"Уведомления {new_status}")