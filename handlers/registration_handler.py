# handlers/registration_handler.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
import logging

# States
WEIGHT, HEIGHT, GENDER, ACTIVITY, TIMEZONE, NOTIF_TIME_START, NOTIF_TIME_END, CITY, CONFIRM = range(9)

# Временное хранилище данных пользователя (в production — лучше в БД или через context.user_data)
# Но пока будем использовать context.user_data

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text("Введите ваш вес (кг, от 30 до 200):")
    return WEIGHT

async def weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите число.")
        return WEIGHT
    weight = int(text)
    if not (30 <= weight <= 200):
        await update.message.reply_text("Вес должен быть от 30 до 200 кг.")
        return WEIGHT
    context.user_data["weight"] = weight
    await update.message.reply_text("Введите ваш рост (см, от 100 до 250):")
    return HEIGHT

async def height_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("Пожалуйста, введите число.")
        return HEIGHT
    height = int(text)
    if not (100 <= height <= 250):
        await update.message.reply_text("Рост должен быть от 100 до 250 см.")
        return HEIGHT
    context.user_data["height"] = height
    keyboard = [
        [InlineKeyboardButton("👨 Мужской", callback_data="male")],
        [InlineKeyboardButton("👩 Женский", callback_data="female")]
    ]
    await update.message.reply_text("Выберите пол:", reply_markup=InlineKeyboardMarkup(keyboard))
    return GENDER

async def gender_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = "male" if query.data == "male" else "female"
    context.user_data["gender"] = gender
    keyboard = [
        [InlineKeyboardButton("🐢 Низкая", callback_data="low")],
        [InlineKeyboardButton("🚶 Средняя", callback_data="medium")],
        [InlineKeyboardButton("🏃 Высокая", callback_data="high")]
    ]
    await query.edit_message_text("Выберите уровень активности:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ACTIVITY

async def activity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    activity_map = {"low": "низкая", "medium": "средняя", "high": "высокая"}
    context.user_data["activity_level"] = activity_map[query.data]
    
    # Упрощённый выбор часового пояса (в ТЗ — 11 поясов РФ + другой)
    tz_buttons = [
        [InlineKeyboardButton("Москва", callback_data="Europe/Moscow")],
        [InlineKeyboardButton("Самара", callback_data="Europe/Samara")],
        [InlineKeyboardButton("Екатеринбург", callback_data="Asia/Yekaterinburg")],
        [InlineKeyboardButton("Омск", callback_data="Asia/Omsk")],
        [InlineKeyboardButton("Красноярск", callback_data="Asia/Krasnoyarsk")],
        [InlineKeyboardButton("Иркутск", callback_data="Asia/Irkutsk")],
        [InlineKeyboardButton("Якутск", callback_data="Asia/Yakutsk")],
        [InlineKeyboardButton("Владивосток", callback_data="Asia/Vladivostok")],
        [InlineKeyboardButton("Магадан", callback_data="Asia/Magadan")],
        [InlineKeyboardButton("Камчатка", callback_data="Asia/Kamchatka")],
        [InlineKeyboardButton("Калининград", callback_data="Europe/Kaliningrad")],
        [InlineKeyboardButton("🌍 Другой", callback_data="other_tz")]
    ]
    # Разбиваем на 2 столбца (по 6 кнопок)
    keyboard = []
    for i in range(0, len(tz_buttons), 2):
        row = tz_buttons[i:i+2]
        keyboard.append([btn[0] for btn in row])
    
    await query.edit_message_text("Выберите ваш часовой пояс:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TIMEZONE

async def timezone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tz = query.data
    if tz == "other_tz":
        await query.edit_message_text("Введите часовой пояс в формате Region/City (например, Europe/London):")
        return TIMEZONE
    context.user_data["timezone"] = tz
    await query.edit_message_text("Введите время начала уведомлений (ЧЧ:ММ) или нажмите «🕗 Стандарт»:", 
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🕗 Стандарт (08:00–22:00)", callback_data="standard_time")]]))
    return NOTIF_TIME_START

async def timezone_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обработка ручного ввода часового пояса
    tz = update.message.text.strip()
    # Здесь можно добавить валидацию через pytz.all_timezones, но пока пропустим
    context.user_data["timezone"] = tz
    await update.message.reply_text("Введите время начала уведомлений (ЧЧ:ММ) или нажмите «🕗 Стандарт»:",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🕗 Стандарт (08:00–22:00)", callback_data="standard_time")]]))
    return NOTIF_TIME_START

async def notif_time_start_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query and query.data == "standard_time":
        await query.answer()
        context.user_data["notification_start"] = "08:00"
        context.user_data["notification_end"] = "22:00"
        await query.edit_message_text("Укажите ваш город (опционально) или нажмите «⏭ Пропустить»:",
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Пропустить", callback_data="skip_city")]]))
        return CITY
    else:
        # Ожидаем текстовое сообщение (ЧЧ:ММ)
        text = update.message.text
        if not validate_time(text):
            await update.message.reply_text("Неверный формат времени. Используйте ЧЧ:ММ (например, 09:30).")
            return NOTIF_TIME_START
        context.user_data["notification_start"] = text
        await update.message.reply_text("Введите время окончания уведомлений (ЧЧ:ММ):")
        return NOTIF_TIME_END

async def notif_time_end_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not validate_time(text):
        await update.message.reply_text("Неверный формат времени. Используйте ЧЧ:ММ (например, 22:00).")
        return NOTIF_TIME_END
    context.user_data["notification_end"] = text
    await update.message.reply_text("Укажите ваш город (опционально) или нажмите «⏭ Пропустить»:",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Пропустить", callback_data="skip_city")]]))
    return CITY

async def city_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query and query.data == "skip_city":
        await query.answer()
        context.user_data["city"] = None
    else:
        context.user_data["city"] = update.message.text.strip()
    
    # Подтверждение
    user = context.user_data
    profile = (
        f"✅ Подтверждение профиля:\n"
        f"Вес: {user['weight']} кг\n"
        f"Рост: {user['height']} см\n"
        f"Пол: {'Мужской' if user['gender'] == 'male' else 'Женский'}\n"
        f"Активность: {user['activity_level']}\n"
        f"Часовой пояс: {user['timezone']}\n"
        f"Уведомления: с {user['notification_start']} до {user['notification_end']}\n"
        f"Город: {user.get('city', 'Не указан')}"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Сохранить", callback_data="confirm_save")],
        [InlineKeyboardButton("🔁 Изменить", callback_data="edit_profile")]
    ]
    if query:
        await query.edit_message_text(profile, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(profile, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM

async def confirm_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = context.user_data
    user_data["user_id"] = query.from_user.id

    from database.db_manager import save_user
    save_user(user_data)

    await query.edit_message_text("✅ Регистрация завершена! Ваши данные сохранены.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END

def validate_time(time_str: str) -> bool:
    try:
        h, m = map(int, time_str.split(":"))
        return 0 <= h <= 23 and 0 <= m <= 59
    except:
        return False