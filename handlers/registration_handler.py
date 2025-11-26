from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from database.db_manager import DatabaseManager
from services.weather_service import validate_city

# Состояния
WEIGHT, HEIGHT, GENDER, ACTIVITY, TIMEZONE, TIMEZONE_TEXT_INPUT, NOTIF_TIME_START, NOTIF_TIME_END, CITY, CONFIRM = range(10)

# --- Вспомогательные функции для отображения сообщений ---

async def _show_weight_message(query, context):
    """Показывает сообщение для ввода веса"""
    text = "Введите ваш вес (в кг, от 30 до 200):"
    await query.edit_message_text(text)

async def _send_height_message(update, context):
    """Отправляет новое сообщение для ввода роста"""
    text = f"✅ Вес: {context.user_data['weight']} кг\nВведите ваш рост (в см, от 100 до 250):"
    await update.message.reply_text(text)

async def _show_gender_message(query, context):
    """Показывает сообщение для выбора пола"""
    text = "Выберите ваш пол:"
    keyboard = [
        [InlineKeyboardButton("👨 Мужской", callback_data="gender_male")],
        [InlineKeyboardButton("👩 Женский", callback_data="gender_female")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def _send_gender_message(update, context):
    """Отправляет новое сообщение для выбора пола"""
    text = "Выберите ваш пол:"
    keyboard = [
        [InlineKeyboardButton("👨 Мужской", callback_data="gender_male")],
        [InlineKeyboardButton("👩 Женский", callback_data="gender_female")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def _show_activity_message(query, context):
    """Показывает сообщение для выбора активности"""
    text = "Выберите уровень активности:"
    keyboard = [
        [InlineKeyboardButton("🐢 Низкая", callback_data="act_low")],
        [InlineKeyboardButton("🚶 Средняя", callback_data="act_medium")],
        [InlineKeyboardButton("🏃 Высокая", callback_data="act_high")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def _show_timezone_message(query, context):
    """Показывает сообщение для выбора часового пояса"""
    text = "Выберите ваш часовой пояс:"
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
        ]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def _show_notification_time_start_message(query, context):
    """Показывает сообщение для ввода времени начала уведомлений"""
    text = "Введите время начала уведомлений (ЧЧ:ММ, например, 08:00), или нажмите кнопку:"
    keyboard = [
        [InlineKeyboardButton("🕗 Стандарт (08:00–22:00)", callback_data="standard_time")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def _send_notification_time_end_message(update, context):
    """Отправляет новое сообщение для ввода времени окончания"""
    text = "Введите время окончания уведомлений (ЧЧ:ММ):"
    await update.message.reply_text(text)

async def _show_city_message(query, context):
    """Показывает сообщение для ввода города"""
    text = "Введите ваш город (или нажмите 'Пропустить'):"
    keyboard = [
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_city")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def _send_city_message(update, context):
    """Отправляет новое сообщение для ввода города"""
    text = "Введите ваш город (или нажмите 'Пропустить'):"
    keyboard = [
        [InlineKeyboardButton("⏭ Пропустить", callback_data="skip_city")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def _show_confirmation(update, context):
    """Показывает экран подтверждения"""
    user_data = context.user_data
    
    # Форматируем данные для отображения
    gender_text = "Мужской" if user_data['gender'] == "male" else "Женский"
    activity_text = {
        "low": "Низкая",
        "medium": "Средняя", 
        "high": "Высокая"
    }.get(user_data['activity_level'], user_data['activity_level'])
    
    profile = (
        f"👤 Ваши данные:\n"
        f"• Вес: {user_data['weight']} кг\n"
        f"• Рост: {user_data['height']} см\n"
        f"• Пол: {gender_text}\n"
        f"• Активность: {activity_text}\n"
        f"• Часовой пояс: {user_data['timezone']}\n"
        f"• Уведомления: {user_data['notification_start']} - {user_data['notification_end']}\n"
        f"• Город: {user_data.get('city', 'Не указан')}"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Сохранить", callback_data="confirm_save")],
        [InlineKeyboardButton("🔁 Изменить", callback_data="change_profile")]
    ]
    
    # Определяем тип update и соответствующий метод отправки
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(profile, reply_markup=InlineKeyboardMarkup(keyboard))
    elif hasattr(update, 'message') and update.message:
        await update.message.reply_text(profile, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # Fallback - пытаемся использовать то, что есть
        await update.edit_message_text(profile, reply_markup=InlineKeyboardMarkup(keyboard))

# --- Основные обработчики ---

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации"""
    query = update.callback_query
    await query.answer()
    await _show_weight_message(query, context)
    return WEIGHT

async def weight_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода веса"""
    try:
        weight = int(update.message.text)
        if not (30 <= weight <= 200):
            await update.message.reply_text("Вес должен быть от 30 до 200 кг.")
            return WEIGHT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число от 30 до 200.")
        return WEIGHT
        
    context.user_data['weight'] = weight
    await _send_height_message(update, context)
    return HEIGHT

async def height_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода роста"""
    try:
        height = int(update.message.text)
        if not (100 <= height <= 250):
            await update.message.reply_text("Рост должен быть от 100 до 250 см.")
            return HEIGHT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число от 100 до 250.")
        return HEIGHT
        
    context.user_data['height'] = height
    await _send_gender_message(update, context)
    return GENDER

async def gender_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора пола"""
    query = update.callback_query
    await query.answer()
    
    if "male" in query.data:
        context.user_data['gender'] = "male"
    else:
        context.user_data['gender'] = "female"
        
    await _show_activity_message(query, context)
    return ACTIVITY

async def activity_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора активности"""
    query = update.callback_query
    await query.answer()
    
    activity_map = {
        "act_low": "low",
        "act_medium": "medium", 
        "act_high": "high"
    }
    context.user_data['activity_level'] = activity_map.get(query.data, "medium")
    await _show_timezone_message(query, context)
    return TIMEZONE

async def timezone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора часового пояса"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "other_tz":
        await query.edit_message_text("Введите часовой пояс в формате Region/City (например, Europe/Moscow):")
        return TIMEZONE_TEXT_INPUT
        
    context.user_data['timezone'] = query.data
    await _show_notification_time_start_message(query, context)
    return NOTIF_TIME_START

async def timezone_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстового ввода часового пояса"""
    tz_input = update.message.text.strip()
    
    # Базовая валидация формата
    if "/" not in tz_input or len(tz_input) < 3:
        await update.message.reply_text("Неверный формат. Пример: Europe/Moscow")
        return TIMEZONE_TEXT_INPUT
        
    context.user_data['timezone'] = tz_input
    
    # Создаем fake query для перехода к следующему шагу
    class FakeQuery:
        def __init__(self, message):
            self.message = message
        async def edit_message_text(self, *args, **kwargs):
            await self.message.reply_text(*args, **kwargs)
    
    fake_query = FakeQuery(update.message)
    await _show_notification_time_start_message(fake_query, context)
    return NOTIF_TIME_START

async def notif_time_start_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода времени начала уведомлений"""
    if update.callback_query:
        # Обработка кнопки "Стандарт"
        query = update.callback_query
        await query.answer()
        
        if query.data == "standard_time":
            context.user_data['notification_start'] = "08:00"
            context.user_data['notification_end'] = "22:00"
            await _show_city_message(query, context)
            return CITY
    else:
        # Обработка текстового ввода
        time_str = update.message.text.strip()
        if not _validate_time_format(time_str):
            await update.message.reply_text("Некорректный формат. Используйте ЧЧ:ММ (например, 08:00)")
            return NOTIF_TIME_START
            
        context.user_data['notification_start'] = time_str
        await _send_notification_time_end_message(update, context)
        return NOTIF_TIME_END

async def notif_time_end_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода времени окончания уведомлений"""
    time_str = update.message.text.strip()
    if not _validate_time_format(time_str):
        await update.message.reply_text("Некорректный формат. Используйте ЧЧ:ММ (например, 22:00)")
        return NOTIF_TIME_END
        
    context.user_data['notification_end'] = time_str
    await _send_city_message(update, context)
    return CITY

async def city_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода города"""
    city = update.message.text.strip()
    
    if not validate_city(city):
        await update.message.reply_text("Город не найден. Проверьте написание или попробуйте другой город:")
        return CITY
        
    context.user_data['city'] = city
    await _show_confirmation(update, context)
    return CONFIRM

async def skip_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск ввода города"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['city'] = None
    await _show_confirmation(query, context)
    return CONFIRM

async def confirm_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение профиля"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = DatabaseManager()
    
    # Используем словарь вместо объекта User
    user_data = {
        "user_id": user_id,
        "weight": context.user_data['weight'],
        "height": context.user_data['height'],
        "gender": context.user_data['gender'],
        "activity_level": context.user_data['activity_level'],
        "timezone": context.user_data['timezone'],
        "notification_start": context.user_data['notification_start'],
        "notification_end": context.user_data['notification_end'],
        "city": context.user_data.get('city'),
        "notifications_enabled": True
    }
    
    db.save_user(user_data)
    await query.edit_message_text("✅ Регистрация завершена! Теперь вы можете использовать бота.")
    
    # Очищаем временные данные
    context.user_data.clear()
    return ConversationHandler.END

async def change_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к редактированию профиля"""
    query = update.callback_query
    await query.answer()
    await _show_weight_message(query, context)
    return WEIGHT

# --- Вспомогательные методы ---

def _validate_time_format(time_str: str) -> bool:
    """Валидация формата времени ЧЧ:ММ"""
    try:
        if len(time_str) != 5 or time_str[2] != ':':
            return False
        hours = int(time_str[:2])
        minutes = int(time_str[3:])
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except ValueError:
        return False

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена регистрации"""
    if update.message:
        await update.message.reply_text("Регистрация отменена.")
    elif update.callback_query:
        await update.callback_query.message.reply_text("Регистрация отменена.")
    context.user_data.clear()
    return ConversationHandler.END