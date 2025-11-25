# handlers/profile_handler.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from database.db_manager import DatabaseManager  # ← Импортируем класс
from services.weather_service import validate_city

# Состояния для мини-диалогов
EDIT_WEIGHT, EDIT_HEIGHT, EDIT_GENDER, EDIT_ACTIVITY, EDIT_TIMEZONE, EDIT_NOTIFICATIONS, EDIT_CITY = range(7)

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
        f"Активность: {user['activity_level']}\n"
        f"Часовой пояс: {user['timezone']}\n"
        f"Уведомления: с {user['notification_start']} до {user['notification_end']}\n"
        f"Город: {user['city'] or 'Не указан'}\n\n"
        f"Выберите поле для редактирования:"
    )
    
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить вес", callback_data="edit_weight")],
        [InlineKeyboardButton("✏️ Изменить рост", callback_data="edit_height")],
        [InlineKeyboardButton("✏️ Изменить пол", callback_data="edit_gender")],
        [InlineKeyboardButton("✏️ Изменить активность", callback_data="edit_activity")],
        [InlineKeyboardButton("✏️ Изменить часовой пояс", callback_data="edit_timezone")],
        [InlineKeyboardButton("✏️ Изменить уведомления", callback_data="edit_notifications")],
        [InlineKeyboardButton("✏️ Изменить город", callback_data="edit_city")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_edit")]
    ]
    
    await query.edit_message_text(profile, reply_markup=InlineKeyboardMarkup(keyboard))

# --- Вес ---
async def start_edit_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите новый вес (в кг, от 30 до 200):")
    return EDIT_WEIGHT

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
    return EDIT_HEIGHT

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
    return EDIT_GENDER

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
    return EDIT_ACTIVITY

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

# --- Часовой пояс ---
async def start_edit_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Показываем кнопки с часовыми поясами (как в регистрации)
    keyboard = [
        [
            InlineKeyboardButton("UTC+3 (Москва)", callback_data="tz:Europe/Moscow"),
            InlineKeyboardButton("UTC+4 (Самара)", callback_data="tz:Europe/Samara")
        ],
        [
            InlineKeyboardButton("UTC+5 (Екатеринбург)", callback_data="tz:Asia/Yekaterinburg"),
            InlineKeyboardButton("UTC+6 (Омск)", callback_data="tz:Asia/Omsk")
        ],
        [
            InlineKeyboardButton("UTC+7 (Красноярск)", callback_data="tz:Asia/Krasnoyarsk"),
            InlineKeyboardButton("UTC+8 (Иркутск)", callback_data="tz:Asia/Irkutsk")
        ],
        [
            InlineKeyboardButton("UTC+9 (Якутск)", callback_data="tz:Asia/Yakutsk"),
            InlineKeyboardButton("UTC+10 (Владивосток)", callback_data="tz:Asia/Vladivostok")
        ],
        [
            InlineKeyboardButton("UTC+11 (Магадан)", callback_data="tz:Asia/Magadan"),
            InlineKeyboardButton("UTC+12 (Камчатка)", callback_data="tz:Asia/Kamchatka")
        ],
        [
            InlineKeyboardButton("🌍 Другой", callback_data="tz:other")
        ]
    ]
    await query.edit_message_text("Выберите ваш часовой пояс:", reply_markup=InlineKeyboardMarkup(keyboard))
    return EDIT_TIMEZONE

async def save_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    tz = query.data.split(":", 1)[1]
    
    if tz == "other":
        await query.edit_message_text("Введите часовой пояс в формате Region/City:")
        return EDIT_TIMEZONE  # Остаться в том же состоянии, но с вводом текста
    
    db = DatabaseManager()
    db.update_user_field(user_id, "timezone", tz)
    await query.edit_message_text(f"✅ Часовой пояс обновлён: {tz}")
    return ConversationHandler.END

async def save_timezone_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tz_input = update.message.text
    # Валидация через pytz (или zoneinfo)
    try:
        import pytz
        if tz_input not in pytz.all_timezones:
            await update.message.reply_text("Неверный формат. Пример: Europe/Moscow")
            return EDIT_TIMEZONE
    except ImportError:
        pass  # если pytz не установлен
    db = DatabaseManager()
    db.update_user_field(user_id, "timezone", tz_input)
    await update.message.reply_text(f"✅ Часовой пояс обновлён: {tz_input}")
    return ConversationHandler.END

# --- Уведомления ---
async def start_edit_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите новое время начала уведомлений (ЧЧ:ММ, например, 08:00):")
    return EDIT_NOTIFICATIONS

async def save_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    if query:
        await query.answer()
        await query.edit_message_text("Введите новое время начала уведомлений (ЧЧ:ММ, например, 08:00):")
        return EDIT_NOTIFICATIONS
    else:
        time_str = update.message.text
        if not (":" in time_str and len(time_str) == 5):
            await update.message.reply_text("Некорректный формат. Пример: 08:00")
            return EDIT_NOTIFICATIONS
        
        context.user_data['temp_start_time'] = time_str
        await update.message.reply_text("Введите новое время окончания уведомлений (ЧЧ:ММ, например, 22:00):")
        return EDIT_NOTIFICATIONS + 1  # следующее состояние — сохранение окончания

async def save_notifications_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    time_str = update.message.text
    if not (":" in time_str and len(time_str) == 5):
        await update.message.reply_text("Некорректный формат. Пример: 22:00")
        return EDIT_NOTIFICATIONS + 1
    
    start_time = context.user_data['temp_start_time']
    end_time = time_str
    db = DatabaseManager()
    db.update_user_field(user_id, "notification_start", start_time)
    db.update_user_field(user_id, "notification_end", end_time)
    await update.message.reply_text(f"✅ Уведомления обновлены: с {start_time} до {end_time}")
    del context.user_data['temp_start_time']
    return ConversationHandler.END

# --- Город ---
async def start_edit_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите новый город (или 'пропустить', чтобы удалить):")
    return EDIT_CITY

async def save_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    city = update.message.text
    if city.lower() == "пропустить":
        city = None
    elif city:
        if not validate_city(city):
            await update.message.reply_text("Город не найден. Попробуйте ещё раз:")
            return EDIT_CITY

    db = DatabaseManager()
    db.update_user_field(user_id, "city", city)
    city_text = city or "не указан"
    await update.message.reply_text(f"✅ Город обновлён: {city_text}")
    return ConversationHandler.END

# --- Отмена ---
async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Редактирование отменено.")
    return ConversationHandler.END