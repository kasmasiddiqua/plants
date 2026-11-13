"""Simple, explainable OpenCV measurements for a front-facing plant photo."""
from pathlib import Path

try:
    import cv2
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - depends on optional runtime package
    cv2 = None
    np = None


def _require_cv2():
    if cv2 is None or np is None:
        raise RuntimeError('Image analysis requires OpenCV and NumPy to be installed. Install the project dependencies first.')


def analyze_image(image_path, reference_height_cm=None):
    _require_cv2()
    if hasattr(image_path, 'read'):
        image_path.seek(0)
        image = cv2.imdecode(np.frombuffer(image_path.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
        image_path.seek(0)
    else:
        image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError('The uploaded file is not a readable image.')
    image = cv2.resize(image, (800, 600))
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Green pixels are a practical baseline for a student project.
    mask = cv2.inRange(hsv, np.array([25, 35, 25]), np.array([95, 255, 255]))
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > 100]
    if not contours:
        return {'height_cm': 0.0, 'leaf_count': 0, 'leaf_area_percent': 0.0,
                'note': 'No clear green plant region was detected; try a brighter image.'}

    plant_contour = max(contours, key=cv2.contourArea)
    x, y, width, height = cv2.boundingRect(plant_contour)
    plant_area = cv2.contourArea(plant_contour)
    leaf_count = sum(1 for contour in contours if cv2.contourArea(contour) > plant_area * 0.025 and contour is not plant_contour)
    pixel_height = max(height, 1)
    height_cm = pixel_height * (reference_height_cm / 600) if reference_height_cm else pixel_height / 30
    leaf_area_percent = min(100.0, plant_area / (image.shape[0] * image.shape[1]) * 100)
    return {'height_cm': round(height_cm, 2), 'leaf_count': leaf_count,
            'leaf_area_percent': round(leaf_area_percent, 2),
            'note': f'Green segmentation detected a plant region at ({x}, {y}); measurements are estimates.'}

def detect_disease(image_path):
    """Return an explainable visual screening result, not a confirmed diagnosis."""
    _require_cv2()
    if hasattr(image_path, 'read'):
        image_path.seek(0)
        image = cv2.imdecode(np.frombuffer(image_path.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
        image_path.seek(0)
    else:
        image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError('The uploaded file is not a readable image.')

    image = cv2.resize(image, (800, 600))
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, np.array([25, 35, 25]), np.array([95, 255, 255])) > 0
    plant_pixels = int(green.sum())
    if plant_pixels < 400:
        return {
            'label': 'No clear plant detected', 'confidence': 0,
            'severity': 'unknown', 'symptoms': 'The image does not contain enough visible green leaf area to screen.',
            'guidance': 'Upload a well-lit close-up of several leaves, including the front and underside.',
        }

    yellow = cv2.inRange(hsv, np.array([15, 45, 60]), np.array([40, 255, 255])) > 0
    brown = cv2.inRange(hsv, np.array([0, 45, 25]), np.array([25, 255, 180])) > 0
    dark = (hsv[:, :, 2] < 75) & (hsv[:, :, 1] > 35)
    yellow_ratio = float((yellow & green).sum()) / plant_pixels
    brown_ratio = float((brown & green).sum()) / plant_pixels
    dark_ratio = float((dark & green).sum()) / plant_pixels

    if yellow_ratio > 0.20:
        label = 'Possible chlorosis or nutrient stress'
        symptoms = 'A large yellow area was detected across the visible green region.'
        guidance = 'Check watering and drainage first, then inspect roots and the undersides of leaves for pests.'
        severity = 'watch'
        signal = yellow_ratio
    elif brown_ratio > 0.12 or dark_ratio > 0.10:
        label = 'Possible leaf spot or fungal stress'
        symptoms = 'Brown or dark patches were detected on the visible leaf region.'
        guidance = 'Isolate the plant, remove badly affected leaves with clean tools, and improve airflow. Confirm the cause before treatment.'
        severity = 'attention'
        signal = max(brown_ratio, dark_ratio)
    else:
        label = 'No obvious disease pattern detected'
        symptoms = 'The visible leaf colors are mostly consistent with healthy green tissue.'
        guidance = 'Keep monitoring new growth and rescan a clear close-up if spots, curling, or discoloration appear.'
        severity = 'healthy'
        signal = max(yellow_ratio, brown_ratio, dark_ratio)

    confidence = round(min(96, max(58, 58 + signal * 180)), 1)
    return {
        'label': label, 'confidence': confidence, 'severity': severity,
        'symptoms': symptoms, 'guidance': guidance,
    }
