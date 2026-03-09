"""
Common helper functions
"""

import re
import json
import hashlib
import random
import string
import logging
from typing import Optional, List, Dict, Any, Tuple, Union, Callable
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo, available_timezones

from telegram import Update, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from common.constants import (
    MAX_MESSAGE_LENGTH, PROGRESS_SYMBOLS, EMOJI_MAP,
    TIME_FORMATS, LOADING_ANIMATIONS
)

logger = logging.getLogger(__name__)


def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
    """Split long message into chunks"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


async def safe_send_message(
    update: Update,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = ParseMode.MARKDOWN,
    disable_web_page_preview: bool = True
) -> bool:
    """Safely send message with error handling"""
    try:
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview
                )
                return True
            except Exception as e:
                # If edit fails, try sending new message
                logger.debug(f"Failed to edit message, sending new: {e}")
                await update.callback_query.message.reply_text(
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview
                )
                return True
        else:
            await update.message.reply_text(
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview
            )
            return True
    except Exception as e:
        # Fallback to plain text if markdown fails
        if parse_mode == ParseMode.MARKDOWN:
            return await safe_send_message(update, escape_markdown(text), reply_markup, None)
        else:
            logger.error(f"Failed to send message: {e}")
            return False


async def safe_edit_message(
    query,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = ParseMode.MARKDOWN
) -> bool:
    """Safely edit message with error handling"""
    try:
        await query.edit_message_text(
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        return True
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        return False


def get_user_locale(update: Update) -> str:
    """Get user's language preference from Telegram"""
    if update and update.effective_user:
        lang_code = update.effective_user.language_code
        if lang_code and lang_code.lower().startswith("ru"):
            return "ru"
    return "en"


def format_number(num: Union[int, float], lang: str = "ru", decimals: int = 0) -> str:
    """Format number with thousand separators"""
    if isinstance(num, float):
        num = round(num, decimals)
        if decimals == 0:
            num = int(num)
    
    if lang == "ru":
        return f"{num:,}".replace(",", " ")
    return f"{num:,}"


def parse_time(time_str: str) -> Optional[Tuple[int, int]]:
    """Parse time string (HH:MM) to (hour, minute)"""
    match = re.match(r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$', time_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def parse_date(date_str: str) -> Optional[date]:
    """Parse date string in various formats"""
    formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None


def get_local_time(user_timezone: str = "UTC") -> datetime:
    """Get current time in user's timezone"""
    try:
        tz = ZoneInfo(user_timezone)
        return datetime.now(tz)
    except:
        return datetime.utcnow()


def get_local_date(user_timezone: str = "UTC") -> date:
    """Get current date in user's timezone"""
    return get_local_time(user_timezone).date()


def format_datetime(dt: datetime, format_key: str = "full", lang: str = "ru") -> str:
    """Format datetime according to locale"""
    fmt = TIME_FORMATS.get(format_key, TIME_FORMATS["full"])
    
    # Localize month names for Russian
    if lang == "ru":
        months = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
            5: "мая", 6: "июня", 7: "июля", 8: "августа",
            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }
        weekdays = {
            0: "понедельник", 1: "вторник", 2: "среда", 3: "четверг",
            4: "пятница", 5: "суббота", 6: "воскресенье"
        }
        
        if format_key == "month_year":
            return f"{months[dt.month]} {dt.year}"
        elif format_key == "weekday":
            return weekdays[dt.weekday()]
    
    return dt.strftime(fmt)


def get_progress_bar(
    current: int,
    total: int,
    width: int = 10,
    show_percent: bool = False
) -> str:
    """Generate text-based progress bar"""
    if total <= 0:
        bar = PROGRESS_SYMBOLS["empty"] * width
    else:
        percent = min(current / total, 1.0)
        filled = int(percent * width)
        
        if percent >= 1.0:
            bar = PROGRESS_SYMBOLS["full"] * width
        else:
            bar = PROGRESS_SYMBOLS["full"] * filled + PROGRESS_SYMBOLS["empty"] * (width - filled)
    
    if show_percent:
        percent_val = (current / total * 100) if total > 0 else 0
        return f"{bar} {percent_val:.0f}%"
    
    return bar


def get_loading_animation(step: int) -> str:
    """Get loading animation frame"""
    return LOADING_ANIMATIONS[step % len(LOADING_ANIMATIONS)]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def generate_id(length: int = 8) -> str:
    """Generate random ID"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def hash_string(text: str) -> str:
    """Create hash of string"""
    return hashlib.sha256(text.encode()).hexdigest()


def group_by(lst: List[Any], key_func: Callable) -> Dict[Any, List[Any]]:
    """Group list by key function"""
    result = {}
    for item in lst:
        key = key_func(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def format_emoji(name: str) -> str:
    """Get emoji by name"""
    return EMOJI_MAP.get(name, "")


def json_dumps(data: Any) -> str:
    """JSON dump with date handling"""
    def json_serial(obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    return json.dumps(data, default=json_serial, ensure_ascii=False, indent=2)


def json_loads(data: str) -> Any:
    """JSON load with date handling"""
    return json.loads(data)


def validate_timezone(tz_name: str) -> bool:
    """Validate timezone string"""
    try:
        ZoneInfo(tz_name)
        return tz_name in available_timezones()
    except:
        return False


def get_timezone_offset(tz_name: str) -> Optional[float]:
    """Get timezone offset in hours"""
    try:
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        offset = now.utcoffset()
        if offset:
            return offset.total_seconds() / 3600
    except:
        pass
    return None


def parse_telegram_command(text: str) -> Tuple[str, str]:
    """Parse telegram command into command and args"""
    if not text or not text.startswith('/'):
        return "", text
    
    parts = text.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    return command, args


def extract_mention(text: str) -> Optional[str]:
    """Extract username mention from text"""
    match = re.search(r'@(\w+)', text)
    return match.group(1) if match else None


def extract_number(text: str) -> Optional[float]:
    """Extract number from text"""
    match = re.search(r'[-+]?\d*\.?\d+', text)
    return float(match.group()) if match else None


def format_phone(phone: str) -> str:
    """Format phone number"""
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 11:
        return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    elif len(digits) == 10:
        return f"+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
    else:
        return phone


def format_bytes(bytes_num: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"


def create_callback_data(*args) -> str:
    """Create callback data from arguments"""
    return "_".join(str(arg) for arg in args)


def parse_callback_data(data: str) -> List[str]:
    """Parse callback data into list"""
    return data.split("_")