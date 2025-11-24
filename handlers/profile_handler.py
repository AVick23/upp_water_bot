# handlers/profile_handler.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from database.db_manager import DatabaseManager  # ← Импортируем класс

# Состояния для мини-диалогов
EDIT_WEIGHT, EDIT_HEIGHT, EDIT_GENDER, EDIT_ACTIVITY = range(4)

async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = DatabaseManager()
    user = db.get_user(user_id)
    
    if not user:
        await query.edit_message_text("Ошибка: профиль не найден.")
        return

    profile = (
        f"✏️ Текущие данные:\n"
        f"Вес: {user['weight']} кг\n"
        f"Рост: {user['height']} см\n"
        f"Пол: {'Мужской' if user['gender'] == 'male' else 'Женский'}\n"
        f"Активность: {user['activity_level']}\n\n"
        f"Выберите поле для редактирования:"
    )
    
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить вес", callback_data="edit_weight")],
        [InlineKeyboardButton("✏️ Изменить рост", callback_data="edit_height")],
        [InlineKeyboardButton("✏️ Изменить пол", callback_data="edit_gender")],
        [InlineKeyboardButton("✏️ Изменить активность", callback_data="edit_activity")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_edit")]
    ]
    
    await query.edit_message_text(profile, reply_markup=InlineKeyboardMarkup(keyboard))

# --- Вес ---
async def start_edit_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите новый вес (в кг, от 30 до 200):")

async def save_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        weight = int(update.message.text)
        if not (30 <= weight <= 200):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Некорректный вес. Введите число от 30 до 200.")
        return EDIT_WEIGHT

    db = DatabaseManager()
    db.update_user_field(user_id, "weight", weight)
    await update.message.reply_text(f"✅ Вес обновлён: {weight} кг")
    return ConversationHandler.END

# --- Рост ---
async def start_edit_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите новый рост (в см, от 100 до 250):")

async def save_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        height = int(update.message.text)
        if not (100 <= height <= 250):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Некорректный рост. Введите число от 100 до 250.")
        return EDIT_HEIGHT

    db = DatabaseManager()
    db.update_user_field(user_id, "height", height)
    await update.message.reply_text(f"✅ Рост обновлён: {height} см")
    return ConversationHandler.END

# --- Пол ---
async def start_edit_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("👨 Мужской", callback_data="edit_gender:male")],
        [InlineKeyboardButton("👩 Женский", callback_data="edit_gender:female")]
    ]
    await query.edit_message_text("Выберите пол:", reply_markup=InlineKeyboardMarkup(keyboard))

async def save_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    gender = query.data.split(":")[1]
    
    db = DatabaseManager()
    db.update_user_field(user_id, "gender", gender)
    text = "✅ Пол обновлён: Мужской" if gender == "male" else "✅ Пол обновлён: Женский"
    await query.edit_message_text(text)
    return ConversationHandler.END

# --- Активность ---
async def start_edit_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🐢 Низкая", callback_data="edit_activity:low")],
        [InlineKeyboardButton("🚶 Средняя", callback_data="edit_activity:medium")],
        [InlineKeyboardButton("🏃 Высокая", callback_data="edit_activity:high")]
    ]
    await query.edit_message_text("Выберите уровень активности:", reply_markup=InlineKeyboardMarkup(keyboard))

async def save_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    activity = query.data.split(":")[1]
    
    db = DatabaseManager()
    db.update_user_field(user_id, "activity_level", activity)
    activity_text = {"low": "Низкая", "medium": "Средняя", "high": "Высокая"}
    await query.edit_message_text(f"✅ Активность обновлена: {activity_text[activity]}")
    return ConversationHandler.END

# --- Отмена ---
async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Редактирование отменено.")
    return ConversationHandler.END