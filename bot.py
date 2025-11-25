import logging
import warnings
from telegram.warnings import PTBUserWarning
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from config.settings import BOT_TOKEN
from handlers.start_handler import start
from handlers.stats_handler import stats
from handlers.notifications_handler import notifications, toggle_notifications
from handlers.water_handler import handle_water_button
from handlers.stats_handler import handle_stats_period

# Регистрация обработчиков регистрации
from handlers.registration_handler import (
    start_registration, weight_input, height_input, gender_input,
    activity_input, timezone_input, timezone_text_input,
    notif_time_start_input, notif_time_end_input, city_input,
    confirm_save, cancel, WEIGHT, HEIGHT, GENDER, ACTIVITY,
    TIMEZONE, NOTIF_TIME_START, NOTIF_TIME_END, CITY, CONFIRM
)

# Регистрация обработчиков редактирования профиля
from handlers.profile_handler import (
    edit_profile, start_edit_weight, save_weight,
    start_edit_height, save_height,
    start_edit_gender, save_gender,
    start_edit_activity, save_activity,
    start_edit_timezone, save_timezone, save_timezone_text,
    start_edit_notifications, save_notifications, save_notifications_end,
    start_edit_city, save_city,
    cancel_edit,
    EDIT_WEIGHT, EDIT_HEIGHT, EDIT_GENDER, EDIT_ACTIVITY, EDIT_TIMEZONE, EDIT_NOTIFICATIONS, EDIT_CITY
)

# Джобы
from jobs.reminder_job import check_and_send_reminders

from database.models import init_db

# Подавление предупреждения per_message
warnings.filterwarnings("ignore", category=PTBUserWarning, message=r".*per_message.*")

# Логирование
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

def main():
    init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    # --- Мини-диалоги для редактирования одного поля ---
    edit_weight_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_weight, pattern="^edit_weight$")],
        states={EDIT_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_weight)]},
        fallbacks=[CallbackQueryHandler(cancel_edit, pattern="^cancel_edit$")]
    )

    edit_height_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_height, pattern="^edit_height$")],
        states={EDIT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_height)]},
        fallbacks=[CallbackQueryHandler(cancel_edit, pattern="^cancel_edit$")]
    )

    edit_gender_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_gender, pattern="^edit_gender$")],
        states={EDIT_GENDER: [CallbackQueryHandler(save_gender, pattern=r"^edit_gender:.+$")]},
        fallbacks=[CallbackQueryHandler(cancel_edit, pattern="^cancel_edit$")]
    )

    edit_activity_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_activity, pattern="^edit_activity$")],
        states={EDIT_ACTIVITY: [CallbackQueryHandler(save_activity, pattern=r"^edit_activity:.+$")]},
        fallbacks=[CallbackQueryHandler(cancel_edit, pattern="^cancel_edit$")]
    )

    # --- НОВЫЕ Конверсации ---
    edit_timezone_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_timezone, pattern="^edit_timezone$")],
        states={
            EDIT_TIMEZONE: [
                CallbackQueryHandler(save_timezone, pattern=r"^tz:.+$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_timezone_text)
            ]
        },
        fallbacks=[CallbackQueryHandler(cancel_edit, pattern="^cancel_edit$")]
    )

    edit_notifications_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_notifications, pattern="^edit_notifications$")],
        states={
            EDIT_NOTIFICATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_notifications)],
            EDIT_NOTIFICATIONS + 1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_notifications_end)]
        },
        fallbacks=[CallbackQueryHandler(cancel_edit, pattern="^cancel_edit$")]
    )

    edit_city_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_city, pattern="^edit_city$")],
        states={EDIT_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_city)]},
        fallbacks=[CallbackQueryHandler(cancel_edit, pattern="^cancel_edit$")]
    )

    # --- Основной диалог регистрации ---
    registration_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_registration, pattern="^start_reg$")],
        states={
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_input)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height_input)],
            GENDER: [CallbackQueryHandler(gender_input)],
            ACTIVITY: [CallbackQueryHandler(activity_input)],
            TIMEZONE: [
                CallbackQueryHandler(timezone_input, pattern=r"^(?!other_tz).*$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, timezone_text_input)
            ],
            NOTIF_TIME_START: [
                CallbackQueryHandler(notif_time_start_input, pattern="^standard_time$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, notif_time_start_input)
            ],
            NOTIF_TIME_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, notif_time_end_input)],
            CITY: [
                CallbackQueryHandler(city_input, pattern="^skip_city$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, city_input)
            ],
            CONFIRM: [CallbackQueryHandler(confirm_save, pattern="^confirm_save$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # --- Регистрация команд ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("notifications", notifications))

    # --- Мини-диалоги ---
    application.add_handler(edit_weight_conv)
    application.add_handler(edit_height_conv)
    application.add_handler(edit_gender_conv)
    application.add_handler(edit_activity_conv)
    application.add_handler(edit_timezone_conv)  # ← НОВОЕ
    application.add_handler(edit_notifications_conv)  # ← НОВОЕ
    application.add_handler(edit_city_conv)  # ← НОВОЕ

    # --- Регистрация основного диалога и кнопок ---
    application.add_handler(registration_conv)
    application.add_handler(CallbackQueryHandler(edit_profile, pattern="^edit_profile$"))
    application.add_handler(CallbackQueryHandler(handle_water_button, pattern="^drank_water$"))
    application.add_handler(CallbackQueryHandler(toggle_notifications, pattern="^notif_(enable|disable)$"))
    application.add_handler(CallbackQueryHandler(handle_stats_period, pattern=r"^stats_(today|week|month)$"))

    # --- Сканирующий джоб для ежедневных напоминаний ---
    application.job_queue.run_repeating(check_and_send_reminders, interval=300)

    # Запуск
    application.run_polling()

if __name__ == "__main__":
    main()