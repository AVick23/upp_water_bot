"""
Common handlers (error handler, help, etc)
"""

import logging
import traceback
import html
import json
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Locale
from common.helpers import get_user_locale, safe_send_message, split_message
from common.middleware import get_middleware_stats
from common.decorators import admin_only

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    # Log error
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    logger.error(f"Traceback: {tb_string}")
    
    # Notify user
    if update and update.effective_message:
        lang = get_user_locale(update)
        L = Locale.RU if lang == "ru" else Locale.EN
        
        try:
            await safe_send_message(
                update,
                L["error_unknown"],
                parse_mode=None
            )
        except:
            pass
    
    # Notify admins
    try:
        from config import config
        admin_ids = getattr(config, "ADMIN_IDS", [])
        
        if admin_ids:
            error_text = (
                f"❌ *Error in bot*\n\n"
                f"*Update:* {update}\n"
                f"*Error:* {context.error}\n\n"
                f"*Traceback:*\n`{html.escape(tb_string[-1000:])}`"
            )
            
            for admin_id in admin_ids:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=error_text,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except:
                    pass
    except:
        pass


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    help_text = (
        "💧 **WaterBot - Помощь**\n\n"
        "**Команды:**\n"
        "/start - Начать / Главное меню\n"
        "/help - Показать эту справку\n"
        "/stats - Статистика\n"
        "/settings - Настройки\n"
        "/cancel - Отмена текущего действия\n\n"
        
        "**Как пользоваться:**\n"
        "1️⃣ Добавьте напиток через кнопку 💧\n"
        "2️⃣ Выберите объём и тип напитка\n"
        "3️⃣ Следите за прогрессом в главном меню\n"
        "4️⃣ Получайте достижения за регулярность\n\n"
        
        "**Особенности:**\n"
        "• Умные напоминания подстраиваются под ваш ритм\n"
        "• Погодная коррекция нормы в жаркие дни\n"
        "• 58 достижений разной редкости\n"
        "• Экспорт данных в CSV и JSON\n\n"
        
        "**Коэффициенты напитков:**\n"
        "Вода: 100% | Чай: 85-95% | Кофе: 65-90%\n"
        "Сок: 70% | Энергетик: 40%\n\n"
        
        "По всем вопросам: @your_support"
    )
    
    keyboard = [[InlineKeyboardButton(L["btn_back"], callback_data="main_menu")]]
    
    await safe_send_message(
        update,
        help_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show about information"""
    # Определяем, откуда пришел вызов
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        message = query.message
        edit = True
    else:
        message = update.message
        edit = False
    
    lang = get_user_locale(update)
    
    if lang == "ru":
        text = (
            "💧 **WaterBot - Водный трекер**\n\n"
            "**Версия:** 2.0.0\n"
            "**Создано:** 2024\n\n"
            
            "**Возможности:**\n"
            "• Умный расчёт нормы воды\n"
            "• Учёт различных напитков\n"
            "• 58 достижений и уровни\n"
            "• Статистика и графики\n"
            "• Напоминания с адаптивным интервалом\n"
            "• Экспорт данных\n\n"
            
            "**Технологии:**\n"
            "• Python 3.10+\n"
            "• python-telegram-bot\n"
            "• SQLAlchemy + aiosqlite\n"
            "• Async/await архитектура\n\n"
            
            "**Исходный код:**\n"
            "https://github.com/yourusername/waterbot\n\n"
            
            "Создано с ❤️ для здорового образа жизни"
        )
    else:
        text = (
            "💧 **WaterBot - Water Tracker**\n\n"
            "**Version:** 2.0.0\n"
            "**Created:** 2024\n\n"
            
            "**Features:**\n"
            "• Smart water norm calculation\n"
            "• Various drinks tracking\n"
            "• 58 achievements and levels\n"
            "• Statistics and charts\n"
            "• Adaptive interval reminders\n"
            "• Data export\n\n"
            
            "**Technologies:**\n"
            "• Python 3.10+\n"
            "• python-telegram-bot\n"
            "• SQLAlchemy + aiosqlite\n"
            "• Async/await architecture\n\n"
            
            "**Source code:**\n"
            "https://github.com/yourusername/waterbot\n\n"
            
            "Made with ❤️ for healthy lifestyle"
        )
    
    keyboard = [[InlineKeyboardButton(Locale.get("btn_back", lang), callback_data="main_menu")]]
    
    if edit:
        await message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current conversation"""
    lang = get_user_locale(update)
    L = Locale.RU if lang == "ru" else Locale.EN
    
    # Clear user data
    context.user_data.clear()
    
    # Cancel any conversation
    await update.message.reply_text(
        L["btn_cancel"],
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Return to main menu - we'll need to implement this
    # from bot.handlers import send_main_menu
    # return await send_main_menu(update, context)
    return


async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    from registration.handlers import send_main_menu
    await send_main_menu(update, context)


@admin_only
async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin statistics"""
    from common.middleware import get_middleware_stats
    
    stats = get_middleware_stats(context.application)
    
    text = (
        "📊 **Admin Statistics**\n\n"
        f"🕐 Uptime: {stats.get('uptime', 'N/A')}\n"
        f"📈 Total updates: {stats.get('total_updates', 0)}\n"
        f"👥 Total users: {stats.get('total_users', 0)}\n"
        f"⚡ Avg response: {stats.get('avg_response_time', 0)*1000:.2f}ms\n\n"
        
        "**Handlers:**\n"
    )
    
    for handler, data in stats.get('handlers', {}).items():
        avg_time = data['total_time'] / data['calls'] * 1000 if data['calls'] > 0 else 0
        text += f"• {handler}: {data['calls']} calls, {avg_time:.1f}ms avg\n"
    
    text += "\n**Errors:**\n"
    for error, count in stats.get('errors', {}).items():
        text += f"• {error}: {count}\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@admin_only
async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    
    # Get all users (you'll need to implement this)
    # from db import get_all_users
    # users = await get_all_users()
    users = []
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"📢 **Broadcast:**\n\n{message}",
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
        except:
            failed += 1
        
        # Rate limiting
        await asyncio.sleep(0.05)
    
    await update.message.reply_text(
        f"Broadcast complete!\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )


@admin_only
async def admin_sql_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute SQL query (dangerous!)"""
    if not context.args:
        await update.message.reply_text("Usage: /sql <query>")
        return
    
    query = ' '.join(context.args)
    
    try:
        # from db import execute_raw_sql
        # result = await execute_raw_sql(query)
        result = None
        
        # Format result
        if isinstance(result, list):
            text = f"✅ Query executed, {len(result)} rows returned:\n"
            text += json.dumps(result[:5], indent=2, default=str)
            if len(result) > 5:
                text += f"\n... and {len(result) - 5} more"
        else:
            text = f"✅ Query executed: {result}"
        
    except Exception as e:
        text = f"❌ Error: {e}"
    
    # Split long messages
    for chunk in split_message(text):
        await update.message.reply_text(chunk, parse_mode=None)