# services/water_calculator.py
import math

def calculate_norm(user_data: dict, temperature: float | None = None) -> int:
    """
    Рассчитывает суточную норму воды с учётом:
    - веса, пола, активности (обязательно),
    - температуры (опционально, из OpenWeatherMap).
    """
    weight = user_data["weight"]
    gender = user_data["gender"]
    activity = user_data["activity_level"]

    base_ml = weight * 30
    gender_coef = 1.1 if gender == "male" else 1.0
    activity_map = {"низкая": 1.0, "средняя": 1.1, "высокая": 1.2}
    activity_coef = activity_map.get(activity, 1.0)

    norm_ml = base_ml * gender_coef * activity_coef

    # Погодная коррекция
    if temperature is not None and temperature > 20:
        extra_degrees = temperature - 20
        bonus_percent = min(30, int(extra_degrees // 5) * 5)  # +5% за каждые 5°C, макс. +30%
        norm_ml *= (1 + bonus_percent / 100)

    # Округление ВВЕРХ до ближайших 250 мл
    norm_ml = math.ceil(norm_ml / 250) * 250
    return int(norm_ml)