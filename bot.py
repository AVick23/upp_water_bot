#!/usr/bin/env python3
"""
WaterBot - Main entry point
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Добавляем путь к родительской папке, чтобы найти пакет water_bot
sys.path.insert(0, str(Path(__file__).parent.parent))

from __init__ import create_bot, run_bot, shutdown_bot

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global reference to shutdown task to prevent multiple creations
_shutdown_task = None


async def async_main():
    """Async main entry point"""
    app = await create_bot()
    
    loop = asyncio.get_running_loop()
    
    def signal_handler():
        global _shutdown_task
        if _shutdown_task is None or _shutdown_task.done():
            logger.info("Signal received, initiating shutdown...")
            _shutdown_task = asyncio.create_task(shutdown_bot(app, loop))
        else:
            logger.info("Shutdown already in progress...")
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await run_bot(app)
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    finally:
        # Ensure shutdown is called if not already
        if _shutdown_task is None or _shutdown_task.done():
            await shutdown_bot(app, loop)
        else:
            await _shutdown_task


def main():
    """Synchronous main entry point"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()