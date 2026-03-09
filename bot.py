#!/usr/bin/env python3
"""
WaterBot - Main entry point
"""

import asyncio
import logging
import signal
import sys
import traceback
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
_app = None


async def async_main():
    """Async main entry point"""
    global _app
    
    try:
        _app = await create_bot()
        
        loop = asyncio.get_running_loop()
        
        def signal_handler():
            global _shutdown_task
            if _shutdown_task is None or _shutdown_task.done():
                logger.info("Signal received, initiating shutdown...")
                _shutdown_task = asyncio.create_task(shutdown_bot(_app, loop))
            else:
                logger.info("Shutdown already in progress...")
        
        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                # Windows doesn't support signal handlers
                logger.warning(f"Signal handler for {sig} not supported on this platform")
        
        try:
            await run_bot(_app)
        except asyncio.CancelledError:
            logger.info("Main task cancelled")
        except Exception as e:
            logger.error(f"Error in bot run: {e}")
            traceback.print_exc()
        finally:
            # Ensure shutdown is called if not already
            if _shutdown_task is None or _shutdown_task.done():
                await shutdown_bot(_app, loop)
            else:
                await _shutdown_task
                
    except Exception as e:
        logger.error(f"Fatal error in async_main: {e}")
        traceback.print_exc()
        raise


def main():
    """Synchronous main entry point"""
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        if loop and not loop.is_closed():
            # Give pending tasks a chance to complete
            pending = asyncio.all_tasks(loop)
            if pending:
                logger.info(f"Waiting for {len(pending)} pending tasks...")
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            loop.close()
            logger.info("Event loop closed")


if __name__ == "__main__":
    main()