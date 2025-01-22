import cv2
import pyrealsense2 as rs
import numpy as np
import time
from ultralytics import YOLO

# Wczytanie modeli YOLO
# Model do wykrywania ludzi
people_model = YOLO("ludzie.pt")
# Model do wykrywania klamek
doorknob_model = YOLO("klamki.pt")

# Inicjalizacja kamery RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 15)
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 15)
pipeline.start(config)

paused = False

# Słownik dla markerów
marker_dict = {
    1: "Marker 1",
    2: "Marker 2",
    3: "Marker 3",
    4: "Marker 4"
}

# Cooldown na otrzymywanie informacji o tym samym markerze (w sekundach)
marker_cooldown = 10
last_detected_time = {}

# Zmienne do kontrolowania wypisywania statusu w konsoli
previous_marker = None
previous_detected = False

# Liczniki klatek
frames_processed = 0
frames_with_marker = 0


def calculate_angle(width, x):
    """Obliczanie kąta odchylenia od środka obrazu."""
    deviation = x - width / 2
    angle = (deviation / (width / 2)) * 90
    return angle


def angle_to_direction(angle):
    """Konwersja kąta na kierunek zegarowy."""
    if -90 <= angle < -75:
        direction = "9 o'clock"
    elif -75 <= angle < -45:
        direction = "10 o'clock"
    elif -45 <= angle < -15:
        direction = "11 o'clock"
    elif -15 <= angle <= 15:
        direction = "12 o'clock"
    elif 15 < angle <= 45:
        direction = "1 o'clock"
    elif 45 < angle <= 75:
        direction = "2 o'clock"
    elif 75 < angle <= 90:
        direction = "3 o'clock"
    else:
        direction = "Unknown"
    return direction


def is_duplicate(circle1, circle2, center_tolerance=15, size_tolerance=0.15):
    """Sprawdza, czy dwa okręgi są duplikatami."""
    (x1, y1, MA1, ma1, _, _, _, _, _) = circle1
    (x2, y2, MA2, ma2, _, _, _, _, _) = circle2

    center_distance = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    if center_distance > center_tolerance:
        return False

    size1 = (MA1 + ma1) / 2
    size2 = (MA2 + ma2) / 2
    if abs(size1 - size2) / size1 > size_tolerance:
        return False

    return True


def detect_inner_circles(binary_image):
    """Wykrywa małe okręgi wewnątrz większego okręgu."""
    detected_circles = cv2.HoughCircles(
        binary_image,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=10,
        param1=50,
        param2=30,
        minRadius=5,
        maxRadius=30
    )

    if detected_circles is not None:
        detected_circles = np.uint16(np.around(detected_circles))
        return detected_circles[0, :]
    return []


def detect_objects(model, frame):
    """
    Wykrywanie obiektów na klatce za pomocą modelu YOLO.
    Zwraca listę wykrytych obiektów i klatkę z naniesionymi detekcjami.
    """
    results = model.predict(source=frame, conf=0.5, iou=0.5, classes=None, device="cpu")
    detections = results[0].boxes.xyxy.cpu().numpy()  # Koordynaty ramki
    confidences = results[0].boxes.conf.cpu().numpy()  # Pewność detekcji
    class_ids = results[0].boxes.cls.cpu().numpy()  # Id klasy

    # Rysowanie detekcji na klatce
    for (box, confidence, class_id) in zip(detections, confidences, class_ids):
        x1, y1, x2, y2 = map(int, box)
        label = f"ID: {int(class_id)} ({confidence:.2f})"
        color = (0, 255, 0) if model == people_model else (255, 0, 0)  # Kolor zależny od modelu
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return frame, detections


def detect_markers(frame, depth_frame):
    """
    Wykrywanie markerów na klatce.
    Dodanie logiki dla wykrycia, odległości oraz szczegółów markerów.
    """
    global previous_marker, previous_detected, frames_processed, frames_with_marker

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    blurred = cv2.GaussianBlur(blurred, (5, 5), 0)
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        13,
        3
    )

    cv2.imshow("Binary Frame", binary)

    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours is None or hierarchy is None:
        return frame, False

    valid_circles = []
    for i, cnt in enumerate(contours):
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        area = cv2.contourArea(cnt)

        if area < 350 or perimeter < 70:
            continue

        circularity = 4 * np.pi * area / (perimeter ** 2)

        if circularity > 0.7:
            try:
                ellipse = cv2.fitEllipse(cnt)
                (x, y), (MA, ma), _ = ellipse
                circularity_ellipse = min(MA, ma) / max(MA, ma)

                if min(MA, ma) < 10 or max(MA, ma) < 50:
                    continue

                if 0.8 <= circularity_ellipse <= 1.2:
                    valid_circles.append((x, y, MA, ma, cnt, ellipse, hierarchy[0][i], area, perimeter))
            except cv2.error as e:
                print("Błąd dopasowania elipsy: ", e)
                continue

    # Sortowanie okręgów po rozmiarze
    valid_circles.sort(key=lambda c: c[2] * c[3], reverse=True)

    return frame, False


try:
    while True:
        if not paused:
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # Wykrywanie markerów
            output_image, found_marker = detect_markers(color_image, depth_frame)

            # Wykrywanie ludzi
            output_image, _ = detect_objects(people_model, output_image)

            # Wykrywanie klamek
            output_image, _ = detect_objects(doorknob_model, output_image)

            cv2.imshow("Detekcja", output_image)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
