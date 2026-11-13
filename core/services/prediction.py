"""Small linear regression predictor based on stored height observations."""
import numpy as np
from sklearn.linear_model import LinearRegression


def predict_next_height(observations):
    rows = list(observations)
    if len(rows) < 2:
        return None
    first_day = rows[0].captured_on
    x = np.array([[(row.captured_on - first_day).days] for row in rows])
    y = np.array([row.estimated_height_cm for row in rows])
    model = LinearRegression().fit(x, y)
    next_day = max(x[-1][0] + 7, x[-1][0] + 1)
    prediction = max(0, float(model.predict([[next_day]])[0]))
    return round(prediction, 2)


def growth_status(growth_percent):
    if growth_percent >= 20:
        return 'good'
    if growth_percent >= 8:
        return 'healthy'
    if growth_percent >= 0:
        return 'normal'
    return 'slow'


def recommendation(status):
    return {
        'good': 'Growth is strong. Continue the current watering and sunlight routine.',
        'healthy': 'Growth looks healthy. Keep monitoring moisture and provide consistent sunlight.',
        'normal': 'Growth is steady. Check soil moisture and capture the next image in 5-7 days.',
        'slow': 'Growth is slow. Review watering, sunlight, pests, and soil conditions; consult an expert if it persists.',
    }.get(status, 'Keep observing the plant regularly.')
