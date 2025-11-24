# services/water_calculator.py
import math


def calculate_norm(user_data, temperature=None):
    """
    Рассчитывает норму воды с учётом:
    - веса (30 мл на кг),
    - пола (мужской ×1.1, женский ×1.0),
    - активности (низкая ×1.0, средняя ×1.1, высокая ×1.2),
    - погоды (+5% за каждые 5°C выше 20°C, макс. +30%),
    - округления вверх до 250 мл.
    """
    base_ml = user_data['weight'] * 30
    gender_coeff = 1.1 if user_data['gender'] == 'male' else 1.0
    activity_coeff = {
        'low': 1.0,
        'medium': 1.1,
        'high': 1.2
    }[user_data['activity_level']]

    norm_ml = base_ml * gender_coeff * activity_coeff

    # Погодная коррекция
    if temperature is not None and temperature > 20:
        extra = min(0.3, 0.05 * ((temperature - 20) // 5))  # +5% за каждые 5°C, макс. +30%
        norm_ml *= (1 + extra)

    # Округление вверх до 250 мл
    norm_ml = math.ceil(norm_ml / 250) * 250

    return int(norm_ml)