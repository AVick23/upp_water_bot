"""
Common decorators for handlers
"""

import functools
import logging
import asyncio
from typing import Callable, Any, Optional
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from db import get_user
from common.helpers import get_user_locale, safe_send_message
from config import Locale

logger = logging.getLogger(__name__)


def require_registration(func: Callable) -> Callable:
    """
    Decorator to ensure user is registered before accessing handler.
    If not registered, redirects to registration.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        try:
            # Check if user exists and is registered
            user = await get_user(user_id)
            
            if not user or not user.registration_complete:
                # Redirect to registration
                from registration.handlers import start_registration
                return await start_registration(update, context)
            
            # Add user to context for easy access
            context.user_data["user"] = user
            context.user_data["user_id"] = user_id
            context.user_data["lang"] = user.language or "ru"
            
            return await func(update, context, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in require_registration decorator: {e}")
            # Fallback to error message
            lang = get_user_locale(update)
            L = Locale.RU if lang == "ru" else Locale.EN
            await safe_send_message(update, L["error_unknown"])
            return
    
    return wrapper


def log_function_call(func: Callable) -> Callable:
    """Decorator to log function calls with timing"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        func_name = func.__name__
        
        logger.debug(f"Calling {func_name}")
        
        try:
            result = await func(*args, **kwargs)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Finished {func_name} in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in {func_name} after {elapsed:.3f}s: {e}")
            raise
    
    return wrapper


def admin_only(func: Callable) -> Callable:
    """Decorator to restrict access to admins"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from config import config
        
        user_id = update.effective_user.id
        admin_ids = getattr(config, "ADMIN_IDS", [])
        
        if user_id not in admin_ids:
            lang = get_user_locale(update)
            L = Locale.RU if lang == "ru" else Locale.EN
            await safe_send_message(update, "⛔ Access denied")
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def rate_limit(limit: int = 5, period: int = 60) -> Callable:
    """
    Rate limiting decorator
    limit: max calls in period (seconds)
    """
    def decorator(func: Callable) -> Callable:
        user_calls = {}
        
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            now = datetime.now()
            
            # Clean old entries
            if user_id in user_calls:
                user_calls[user_id] = [
                    t for t in user_calls[user_id]
                    if (now - t).total_seconds() < period
                ]
            
            # Check limit
            if user_id in user_calls and len(user_calls[user_id]) >= limit:
                lang = get_user_locale(update)
                L = Locale.RU if lang == "ru" else Locale.EN
                await safe_send_message(update, "🐢 " + L["rate_limit"])
                return
            
            # Add call
            if user_id not in user_calls:
                user_calls[user_id] = []
            user_calls[user_id].append(now)
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """Decorator to retry function on error"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__}")
                        await asyncio.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"All retries failed for {func.__name__}: {e}")
            raise last_error
        return wrapper
    return decorator


def timeout(seconds: int = 30) -> Callable:
    """Decorator to add timeout to async function"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {seconds}s")
                raise
        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 300) -> Callable:
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            key = str(args) + str(sorted(kwargs.items()))
            now = datetime.now()
            
            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if (now - timestamp).total_seconds() < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
            
            # Call function
            result = await func(*args, **kwargs)
            cache[key] = (result, now)
            
            # Clean old entries
            for k in list(cache.keys()):
                if (now - cache[k][1]).total_seconds() > ttl_seconds:
                    del cache[k]
            
            return result
        return wrapper
    return decorator


def handle_errors(func: Callable) -> Callable:
    """Decorator to handle errors gracefully"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            
            lang = get_user_locale(update)
            L = Locale.RU if lang == "ru" else Locale.EN
            
            try:
                await safe_send_message(update, L["error_unknown"])
            except:
                pass
            
            return
    return wrapper


def user_context(func: Callable) -> Callable:
    """Decorator to ensure user context is loaded"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user:
            context.user_data["user_id"] = update.effective_user.id
            context.user_data["username"] = update.effective_user.username
            context.user_data["first_name"] = update.effective_user.first_name
            context.user_data["last_name"] = update.effective_user.last_name
            context.user_data["lang"] = get_user_locale(update)
        
        return await func(update, context, *args, **kwargs)
    return wrapper


def send_typing_action(func: Callable) -> Callable:
    """Decorator to send typing action while processing"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        return await func(update, context, *args, **kwargs)
    return wrapper


def send_upload_photo_action(func: Callable) -> Callable:
    """Decorator to send upload photo action"""
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="upload_photo"
        )
        return await func(update, context, *args, **kwargs)
    return wrapper