"""
Middleware for the bot
"""

import time
import logging
from typing import Callable, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes, ApplicationHandlerStop

from common.helpers import get_user_locale

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect bot metrics"""
    
    def __init__(self):
        self.stats = {
            "total_updates": 0,
            "total_time": 0,
            "handlers": defaultdict(lambda: {"calls": 0, "total_time": 0}),
            "errors": defaultdict(int),
            "users": set(),
            "commands": defaultdict(int),
            "start_time": datetime.now()
        }
    
    def record_update(self, handler_name: str, duration: float):
        """Record an update"""
        self.stats["total_updates"] += 1
        self.stats["total_time"] += duration
        self.stats["handlers"][handler_name]["calls"] += 1
        self.stats["handlers"][handler_name]["total_time"] += duration
    
    def record_error(self, error_type: str):
        """Record an error"""
        self.stats["errors"][error_type] += 1
    
    def record_user(self, user_id: int):
        """Record a user"""
        self.stats["users"].add(user_id)
    
    def record_command(self, command: str):
        """Record a command"""
        self.stats["commands"][command] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        now = datetime.now()
        uptime = now - self.stats["start_time"]
        
        return {
            "uptime": str(uptime).split('.')[0],
            "total_updates": self.stats["total_updates"],
            "total_users": len(self.stats["users"]),
            "avg_response_time": self.stats["total_time"] / self.stats["total_updates"] if self.stats["total_updates"] > 0 else 0,
            "handlers": dict(self.stats["handlers"]),
            "errors": dict(self.stats["errors"]),
            "commands": dict(self.stats["commands"]),
        }


class RateLimiter:
    """Rate limiting middleware"""
    
    def __init__(self, max_calls: int = 30, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.user_calls = defaultdict(list)
    
    def is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        now = datetime.now()
        
        # Clean old calls
        self.user_calls[user_id] = [
            t for t in self.user_calls[user_id]
            if (now - t).total_seconds() < self.period
        ]
        
        # Check limit
        if len(self.user_calls[user_id]) >= self.max_calls:
            return True
        
        # Add call
        self.user_calls[user_id].append(now)
        return False


class RequestLogger:
    """Log all requests"""
    
    @staticmethod
    def log(update: Update, handler_name: str, duration: float):
        """Log a request"""
        user = update.effective_user
        chat = update.effective_chat
        
        user_info = f"User {user.id} (@{user.username})" if user else "Unknown user"
        chat_info = f"Chat {chat.id} ({chat.type})" if chat else "Unknown chat"
        
        logger.info(
            f"[{duration*1000:.1f}ms] {handler_name} - {user_info} - {chat_info}"
        )


class MiddlewareManager:
    """Manage middleware chain"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.rate_limiter = RateLimiter()
        self.logger = RequestLogger()
    
    async def process(self, update: Update, context: ContextTypes.DEFAULT_TYPE, handler: Callable):
        """Process update through middleware chain"""
        start_time = time.time()
        handler_name = getattr(handler, "__name__", "unknown")
        
        try:
            # Record user
            if update.effective_user:
                self.metrics.record_user(update.effective_user.id)
            
            # Rate limiting
            if update.effective_user and self.rate_limiter.is_rate_limited(update.effective_user.id):
                lang = get_user_locale(update)
                from config import Locale
                L = Locale.RU if lang == "ru" else Locale.EN
                await update.effective_message.reply_text("🐢 " + L["rate_limit"])
                raise ApplicationHandlerStop()
            
            # Execute handler
            result = await handler(update, context)
            
            # Record metrics
            duration = time.time() - start_time
            self.metrics.record_update(handler_name, duration)
            self.logger.log(update, handler_name, duration)
            
            return result
            
        except ApplicationHandlerStop:
            # Re-raise to stop propagation
            raise
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            error_type = type(e).__name__
            self.metrics.record_error(error_type)
            self.logger.log(update, f"{handler_name} (ERROR: {error_type})", duration)
            
            # Re-raise
            raise


# Global middleware manager
middleware_manager = MiddlewareManager()


async def setup_middleware(application):
    """Setup middleware chain"""
    
    # Store original process_update
    original_process_update = application.process_update
    
    async def process_update_with_middleware(update: Update):
        """Process update with middleware"""
        
        async def handler(update):
            await original_process_update(update)
        
        try:
            await middleware_manager.process(update, None, handler)
        except ApplicationHandlerStop:
            # Stop propagation
            pass
        except Exception as e:
            logger.exception(f"Middleware error: {e}")
    
    # Replace process_update
    application.process_update = process_update_with_middleware
    
    # Store middleware in app data
    application.bot_data["middleware"] = middleware_manager
    application.bot_data["metrics"] = middleware_manager.metrics


def get_middleware_stats(application) -> Dict[str, Any]:
    """Get middleware statistics"""
    if "metrics" in application.bot_data:
        return application.bot_data["metrics"].get_stats()
    return {}