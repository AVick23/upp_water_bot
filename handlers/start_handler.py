# handlers/start_handler.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager  # ← Импортируем класс
from services.water_calculator import calculate_norm
from services.weather_service import get_current_temp


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = DatabaseManager()  # ← Создаём экземпляр
    user = db.get_user(user_id)  # ← Вызываем метод

    if user is None:
        keyboard = [[InlineKeyboardButton("📝 Начать регистрацию", callback_data="start_reg")]]
        await update.message.reply_text(
            "Привет! 👋\nЯ помогу вам отслеживать потребление воды.\n"
            "Для начала пройдите короткую регистрацию.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        # Получаем температуру, если город указан
        temperature = None
        if user.get("city"):
            temperature = get_current_temp(user["city"])

        norm_ml = calculate_norm(user, temperature=temperature)
        glasses = norm_ml // 250

        profile = (
            f"👤 Ваш профиль:\n"
            f"Вес: {user['weight']} кг\n"
            f"Рост: {user['height']} см\n"
            f"Пол: {'Мужской' if user['gender'] == 'male' else 'Женский'}\n"
            f"Активность: {user['activity_level']}\n"
            f"Часовой пояс: {user['timezone']}\n"
            f"Уведомления: с {user['notification_start']} до {user['notification_end']} "
            f"({'включены' if user['notifications_enabled'] else 'отключены'})\n"
            f"Город: {user['city'] or 'Не указан'}"
        )
        if temperature is not None:
            profile += f"\n🌡 Текущая температура: {temperature}°C"

        profile += f"\n\n💧 Ваша норма: {norm_ml} мл ({glasses} стаканов)"

        keyboard = [
            [InlineKeyboardButton("💧 Я выпил (250 мл)", callback_data="drank_water")],
            [InlineKeyboardButton("✏️ Редактировать профиль", callback_data="edit_profile")]
        ]
        await update.message.reply_text(profile, reply_markup=InlineKeyboardMarkup(keyboard))