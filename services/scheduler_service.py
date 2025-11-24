# services/scheduler_service.py
import math
import json
from typing import List

def generate_reminder_schedule(
    notification_start: str,   # "08:00"
    notification_end: str,     # "22:00"
    total_glasses: int         # например, 9
) -> List[str]:
    """
    Генерирует равномерное расписание напоминаний.
    Первое — в start, последнее — в end, остальные — равномерно.
    """
    if total_glasses <= 1:
        return [notification_start]

    start_h, start_m = map(int, notification_start.split(':'))
    end_h, end_m = map(int, notification_end.split(':'))

    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    if end_minutes <= start_minutes:
        end_minutes += 24 * 60  # поддержка перехода через полночь (опционально)

    interval = (end_minutes - start_minutes) / (total_glasses - 1)

    times = []
    for i in range(total_glasses):
        total_min = start_minutes + round(i * interval)
        # Привести обратно в пределы суток
        total_min = total_min % (24 * 60)
        h = total_min // 60
        m = total_min % 60
        times.append(f"{h:02d}:{m:02d}")

    return times