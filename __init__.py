"""
WaterBot - Main package initializer
Registers all handlers and sets up the bot
"""

import asyncio
import logging
from typing import Optional
from registration.handlers import start_registration

from telegram.ext import (
    Application, ApplicationBuilder, PicklePersistence, 
    CommandHandler
)
from telegram.error import TimedOut

from config import config
from db import init_db, close_engine, migrate_legacy_notification_times
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

# Flag to prevent multiple shutdown attempts
_shutting_down = False


async def create_bot() -> Application:
    """
    Create and configure the bot application.
    This is the main initialization function.
    """
    logger.info("Initializing WaterBot...")
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    await migrate_legacy_notification_times()
    
    # Create bot application with persistence
    persistence = PicklePersistence(
        filepath="data/bot_persistence.pkl",
        update_interval=60
    )
    
    # Configure application with timeout settings
    application = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .persistence(persistence)
        .concurrent_updates(True)
        .connection_pool_size(512)
        .pool_timeout(30.0)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
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
    
   
    application.add_handler(CommandHandler("start", start_registration), group=0)

    # Register common handlers
    application.add_handler(CommandHandler("help", help_handler), group=1)
    application.add_handler(CommandHandler("about", about_handler), group=1)
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    logger.info("Bot initialization complete")
    return application


def handle_polling_error(error: Exception) -> None:
    """Handle polling errors - this is a SYNCHRONOUS function"""
    if isinstance(error, TimedOut):
        logger.warning(f"Polling timeout (expected): {error}")
        # Don't log as error, it's expected sometimes
    else:
        logger.error(f"Polling error: {error}")


async def run_bot(application: Application) -> None:
    """
    Run the bot application.
    """
    logger.info("Starting bot polling...")
    
    try:
        await application.initialize()
        await application.start()
        
        # Start polling with error handling - use SYNCHRONOUS function
        await application.updater.start_polling(
            allowed_updates=[
                "message",
                "callback_query",
                "chat_member",
                "my_chat_member"
            ],
            error_callback=handle_polling_error  # Now it's a regular function, not async
        )
        
        logger.info("Bot is running!")
        
        # Keep running until stopped
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Bot run task cancelled")
            raise
            
    except TimedOut as e:
        logger.error(f"Polling timeout error: {e}")
        # Don't raise - let the bot continue running
    except Exception as e:
        logger.error(f"Unexpected error in run_bot: {e}")
        raise


async def shutdown_bot(application: Application, loop: asyncio.AbstractEventLoop) -> None:
    """
    Gracefully shutdown the bot and close all connections.
    """
    global _shutting_down
    
    # Prevent multiple shutdown attempts
    if _shutting_down:
        logger.info("Shutdown already in progress, skipping...")
        return
    
    _shutting_down = True
    logger.info("Shutting down bot...")
    
    # Stop bot with proper checks
    if application.updater:
        try:
            # Check if updater is running before stopping
            if hasattr(application.updater, 'running') and application.updater.running:
                await application.updater.stop()
                logger.info("Updater stopped")
            else:
                logger.info("Updater was not running")
        except Exception as e:
            logger.error(f"Error stopping updater: {e}")
    
    try:
        # Check if application is running before stopping
        if hasattr(application, 'running') and application.running:
            await application.stop()
            logger.info("Application stopped")
        else:
            logger.info("Application was not running")
    except Exception as e:
        logger.error(f"Error stopping application: {e}")
    
    try:
        await application.shutdown()
        logger.info("Application shut down")
    except Exception as e:
        logger.error(f"Error shutting down application: {e}")
    
    # Close database connections
    try:
        await close_engine()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    # Cancel all tasks except current
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    if tasks:
        logger.info(f"Cancelling {len(tasks)} pending tasks...")
        for task in tasks:
            task.cancel()
        
        # Wait for tasks to complete with timeout
        try:
            await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Some tasks did not complete within timeout")
        except Exception as e:
            logger.error(f"Error during task cancellation: {e}")
    
    logger.info("Shutdown complete")
    
    # Don't stop the loop here - let the main function handle it