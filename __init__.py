"""
WaterBot - Main package initializer
Registers all handlers and sets up the bot
"""

import asyncio
import logging
from typing import Optional

from telegram.ext import (
    Application, ApplicationBuilder, PicklePersistence, 
    CommandHandler
)

from config import config
from db import init_db, close_engine, migrate_legacy_notification_times  # Изменено здесь
from common.middleware import setup_middleware

# Import all module initializers
from registration import register_handlers as register_registration
from water import register_handlers as register_water
from stats import register_handlers as register_stats
from achievements import register_handlers as register_achievements
from settings import register_handlers as register_settings
from notifications import register_handlers as register_notifications, register_jobs
from common.handlers import error_handler, help_handler, about_handler

logger = logging.getLogger(__name__)


async def create_bot() -> Application:
    """
    Create and configure the bot application.
    This is the main initialization function.
    """
    logger.info("Initializing WaterBot...")
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()  # Изменено здесь - используем init_db вместо init_engine
    await migrate_legacy_notification_times()
    
    # Create bot application with persistence
    persistence = PicklePersistence(
        filepath="data/bot_persistence.pkl",
        update_interval=60
    )
    
    application = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .persistence(persistence)
        .concurrent_updates(True)
        .build()
    )
    
    # Setup middleware
    await setup_middleware(application)
    
    # Register all handlers from modules
    logger.info("Registering handlers...")
    
    # Each module registers its own handlers
    register_registration(application)
    register_water(application)
    register_stats(application)
    register_achievements(application)
    register_settings(application)
    register_notifications(application)
    
    # Register background jobs
    register_jobs(application)
    
    # Register common handlers
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("about", about_handler))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    logger.info("Bot initialization complete")
    return application


async def run_bot(application: Application) -> None:
    """
    Run the bot application.
    """
    logger.info("Starting bot polling...")
    await application.initialize()
    await application.start()
    
    # Start polling
    await application.updater.start_polling(
        allowed_updates=[
            "message",
            "callback_query",
            "chat_member",
            "my_chat_member"
        ]
    )
    
    logger.info("Bot is running!")
    
    # Keep running until stopped
    while True:
        await asyncio.sleep(1)


async def shutdown_bot(application: Application, loop: asyncio.AbstractEventLoop) -> None:
    """
    Gracefully shutdown the bot and close all connections.
    """
    logger.info("Shutting down bot...")
    
    # Stop bot
    if application.updater:
        await application.updater.stop()
    await application.stop()
    await application.shutdown()
    
    # Close database connections
    await close_engine()
    
    # Cancel all tasks
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info("Shutdown complete")
    loop.stop()