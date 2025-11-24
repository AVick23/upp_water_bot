# handlers/registration_handler.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from database.db_manager import DatabaseManager
from services.weather_service import validate_city

# Состояния
WEIGHT, HEIGHT, GENDER, ACTIVITY, TIMEZONE, TIMEZONE_TEXT_INPUT, NOTIF_TIME_START, NOTIF_TIME_END, CITY, CONFIRM = range(10)

# --- Шаг 1: Вес ---
async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_start")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="edit_weight")]
    ]
    await query.edit_message_text("Введите ваш вес (в кг, от 30 до 200):", reply_markup=InlineKeyboardMarkup(keyboard))
    return WEIGHT

async def weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = int(update.message.text)
        if not (30 <= weight <= 200):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Некорректный вес. Введите число от 30 до 200.")
        return WEIGHT
    context.user_data['weight'] = weight
    keyboard = [
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_weight")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="edit_weight")],
        [InlineKeyboardButton("▶️ Далее", callback_data="next_to_height")]
    ]
    await update.message.reply_text(f"✅ Вес: {weight} кг\nВведите ваш рост (в см, от 100 до 250):", reply_markup=InlineKeyboardMarkup(keyboard))
    return HEIGHT

# --- Шаг 2: Рост ---
async def height_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = int(update.message.text)
        if not (100 <= height <= 250):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Некорректный рост. Введите число от 100 до 250.")
        return HEIGHT
    context.user_data['height'] = height
    keyboard = [
        [InlineKeyboardButton("👨 Мужской", callback_data="gender_male")],
        [InlineKeyboardButton("👩 Женский", callback_data="gender_female")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_height")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="edit_height")]
    ]
    await update.message.reply_text("Выберите ваш пол:", reply_markup=InlineKeyboardMarkup(keyboard))
    return GENDER

# --- Шаг 3: Пол ---
async def gender_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = "male" if "male" in query.data else "female"
    context.user_data['gender'] = gender
    keyboard = [
        [InlineKeyboardButton("🐢 Низкая", callback_data="act_low")],
        [InlineKeyboardButton("🚶 Средняя", callback_data="act_medium")],
        [InlineKeyboardButton("🏃 Высокая", callback_data="act_high")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_gender")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="edit_gender")]
    ]
    await query.edit_message_text("Выберите уровень активности:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ACTIVITY

# --- Шаг 4: Активность ---
async def activity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    activity = query.data.split("_")[1]
    context.user_data['activity_level'] = activity
    # --- Часовой пояс: инлайн-кнопки с понятными обозначениями ---
    keyboard = [
        [
            InlineKeyboardButton("UTC+3 (Москва)", callback_data="Europe/Moscow"),
            InlineKeyboardButton("UTC+4 (Самара)", callback_data="Europe/Samara")
        ],
        [
            InlineKeyboardButton("UTC+5 (Екатеринбург)", callback_data="Asia/Yekaterinburg"),
            InlineKeyboardButton("UTC+6 (Омск)", callback_data="Asia/Omsk")
        ],
        [
            InlineKeyboardButton("UTC+7 (Красноярск)", callback_data="Asia/Krasnoyarsk"),
            InlineKeyboardButton("UTC+8 (Иркутск)", callback_data="Asia/Irkutsk")
        ],
        [
            InlineKeyboardButton("UTC+9 (Якутск)", callback_data="Asia/Yakutsk"),
            InlineKeyboardButton("UTC+10 (Владивосток)", callback_data="Asia/Vladivostok")
        ],
        [
            InlineKeyboardButton("UTC+11 (Магадан)", callback_data="Asia/Magadan"),
            InlineKeyboardButton("UTC+12 (Камчатка)", callback_data="Asia/Kamchatka")
        ],
        [
            InlineKeyboardButton("🌍 Другой", callback_data="other_tz")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_activity")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="edit_activity")]
    ]
    await query.edit_message_text("Выберите ваш часовой пояс:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TIMEZONE

# --- Шаг 5: Часовой пояс ---
async def timezone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tz = query.data
    if tz == "other_tz":
        await query.edit_message_text("Введите часовой пояс в формате Region/City:")
        return TIMEZONE_TEXT_INPUT
    context.user_data['timezone'] = tz
    keyboard = [
        [InlineKeyboardButton("Стандарт (08:00–22:00)", callback_data="standard_time")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_timezone")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="edit_timezone")]
    ]
    await query.edit_message_text("Введите время начала уведомлений (ЧЧ:ММ, например, 08:00), или нажмите кнопку:", reply_markup=InlineKeyboardMarkup(keyboard))
    return NOTIF_TIME_START

async def timezone_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz_input = update.message.text
    # Валидация через pytz (или zoneinfo)
    try:
        import pytz
        if tz_input not in pytz.all_timezones:
            await update.message.reply_text("Неверный формат. Пример: Europe/Moscow")
            return TIMEZONE_TEXT_INPUT
        context.user_data['timezone'] = tz_input
    except ImportError:
        context.user_data['timezone'] = tz_input  # если pytz не установлен
    keyboard = [
        [InlineKeyboardButton("Стандарт (08:00–22:00)", callback_data="standard_time")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_timezone")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="edit_timezone")]
    ]
    await update.message.reply_text("Введите время начала уведомлений (ЧЧ:ММ, например, 08:00), или нажмите кнопку:", reply_markup=InlineKeyboardMarkup(keyboard))
    return NOTIF_TIME_START

# --- Шаг 6: Время начала уведомлений ---
async def notif_time_start_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        if query.data == "standard_time":
            context.user_data['notification_start'] = "08:00"
            context.user_data['notification_end'] = "22:00"
            keyboard = [
                [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_city")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_notif_start")],
                [InlineKeyboardButton("✏️ Изменить", callback_data="edit_notif_start")]
            ]
            await query.edit_message_text("Введите ваш город (или нажмите 'Пропустить'):", reply_markup=InlineKeyboardMarkup(keyboard))
            return CITY
        else:
            await query.edit_message_text("Введите время начала уведомлений (ЧЧ:ММ):")
            return NOTIF_TIME_START
    else:
        time_str = update.message.text
        if not (":" in time_str and len(time_str) == 5):
            await update.message.reply_text("Некорректный формат. Пример: 08:00")
            return NOTIF_TIME_START
        context.user_data['notification_start'] = time_str
        await update.message.reply_text("Введите время окончания уведомлений (ЧЧ:ММ):")
        return NOTIF_TIME_END

# --- Шаг 7: Время окончания уведомлений ---
async def notif_time_end_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_str = update.message.text
    if not (":" in time_str and len(time_str) == 5):
        await update.message.reply_text("Некорректный формат. Пример: 22:00")
        return NOTIF_TIME_END
    context.user_data['notification_end'] = time_str
    keyboard = [
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_city")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_notif_end")],
        [InlineKeyboardButton("✏️ Изменить", callback_data="edit_notif_end")]
    ]
    await update.message.reply_text("Введите ваш город (или нажмите 'Пропустить'):", reply_markup=InlineKeyboardMarkup(keyboard))
    return CITY

# --- Шаг 8: Город ---
async def city_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        if query.data == "skip_city":
            context.user_data['city'] = None
        else:
            await query.edit_message_text("Введите ваш город:")
            return CITY
    else:
        city = update.message.text
        if not validate_city(city):
            await update.message.reply_text("Город не найден. Попробуйте ещё раз:")
            return CITY
        context.user_data['city'] = city

    # Подтверждение
    profile = (
        f"👤 Ваши данные:\n"
        f"Вес: {context.user_data['weight']} кг\n"
        f"Рост: {context.user_data['height']} см\n"
        f"Пол: {'Мужской' if context.user_data['gender'] == 'male' else 'Женский'}\n"
        f"Активность: {context.user_data['activity_level']}\n"
        f"Часовой пояс: {context.user_data['timezone']}\n"
        f"Уведомления: с {context.user_data['notification_start']} до {context.user_data['notification_end']}\n"
        f"Город: {context.user_data['city'] or 'Не указан'}"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Сохранить", callback_data="confirm_save")],
        [InlineKeyboardButton("🔁 Изменить", callback_data="cancel")]
    ]
    await update.message.reply_text(profile, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM

# --- Шаг 9: Подтверждение ---
async def confirm_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db = DatabaseManager()  # ← Создаём экземпляр

    user_data = {
        "user_id": user_id,
        "weight": context.user_data['weight'],
        "height": context.user_data['height'],
        "gender": context.user_data['gender'],
        "activity_level": context.user_data['activity_level'],
        "timezone": context.user_data['timezone'],
        "notification_start": context.user_data['notification_start'],
        "notification_end": context.user_data['notification_end'],
        "city": context.user_data.get('city')
    }

    db.save_user(user_data)  # ← Вызываем метод класса

    await query.edit_message_text("✅ Регистрация завершена! Теперь вы можете использовать бота.")

    # Очистка состояния
    return ConversationHandler.END

# --- Отмена ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END