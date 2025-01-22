import cv2
import pyrealsense2 as rs
import numpy as np
import time
from ultralytics import YOLO
import requests

# Wczytanie modeli YOLO
# Model do wykrywania ludzi
people_model = YOLO("models/ludzie.pt")
# Model do wykrywania klamek
doorknob_model = YOLO("models/klamki.pt")

# Inicjalizacja kamery RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 15)
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 15)
pipeline.start(config)

paused = False

# Słownik dla markerów
marker_dict = {
    1: "Krzesło", # Marker 1
    2: "Ławka", # Marker 2
    3: "Biurko", # Marker 3
    4: "Szafa", # Marker 4
    5: "Kosz na śmieci" # Marker 5
    # Do dodania markery
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
    deviation = x - width / 2
    angle = (deviation / (width / 2)) * 90
    return angle


def angle_to_direction(angle):
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


def update_flask_data(new_marker_name, new_steps, new_direction):
    url = "http://127.0.0.1:5000/api/update"  # Endpoint do aktualizacji danych
    payload = {
        "marker_name": new_marker_name,
        "steps": new_steps,
        "direction": new_direction
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("API updated")
        else:
            print("Error during updating flask's API")
    except Exception as e:
        print(f"Connection error: {e}")



def is_duplicate(circle1, circle2, center_tolerance=15, size_tolerance=0.15):
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
                print("Error fitting ellipse: ", e)
                continue

    filtered_circles = []
    for circle in valid_circles:
        is_duplicate_circle = any(is_duplicate(circle, existing_circle) for existing_circle in filtered_circles)
        if not is_duplicate_circle:
            filtered_circles.append(circle)

    valid_circles = filtered_circles

    valid_circles.sort(key=lambda c: c[2] * c[3], reverse=True)

    detected_markers = False
    marker_results = []
    second_largest_circle = None

    for idx, circle in enumerate(valid_circles):
        id_label = f"ID: {idx}"
        if idx == 0:
            cv2.ellipse(frame, circle[5], (255, 0, 0), 2)
            cv2.putText(frame, id_label, (int(circle[0]), int(circle[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0),
                        2)
        elif idx == 1:
            second_largest_circle = circle
            cv2.ellipse(frame, circle[5], (0, 0, 255), 2)
            cv2.putText(frame, id_label, (int(circle[0]), int(circle[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255),
                        2)

            # Wyznaczenie ROI wokół drugiego największego okręgu
            x_start = max(0, int(circle[0] - circle[2] / 2))
            x_end = min(binary.shape[1], int(circle[0] + circle[2] / 2))
            y_start = max(0, int(circle[1] - circle[3] / 2))
            y_end = min(binary.shape[0], int(circle[1] + circle[3] / 2))

            # Przycinanie obrazu binarnego do ROI
            roi = binary[y_start:y_end, x_start:x_end]

            # Wizualizacja ROI na obrazie
            cv2.rectangle(frame, (x_start, y_start), (x_end, y_end), (255, 255, 0), 2)

            # Wykrywanie małych okręgów w ROI
            inner_circles = detect_inner_circles(roi)
            if inner_circles is not None:
                for inner_circle in inner_circles:
                    # Offset współrzędnych wewnętrznych okręgów względem ROI
                    offset_x = x_start
                    offset_y = y_start
                    cv2.circle(frame, (inner_circle[0] + offset_x, inner_circle[1] + offset_y), inner_circle[2],
                               (0, 255, 255), 2)

        else:
            cv2.ellipse(frame, circle[5], (0, 255, 0), 2)
            cv2.putText(frame, id_label, (int(circle[0]), int(circle[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                        2)

    if second_largest_circle:
        depth_value = depth_frame.get_distance(int(second_largest_circle[0]), int(second_largest_circle[1]))
        distance = f"{depth_value:.2f}m" if depth_value != 0 else "Unknown"
        steps = f"{round(depth_value * 1.31)} steps" if depth_value != 0 else "Unknown"

        if depth_value <= 5:
            unique_inner_counts = len(inner_circles)

            if unique_inner_counts in marker_dict:
                marker_name = marker_dict[unique_inner_counts]
                color = (0, 255, 0)
            else:
                marker_name = "Unknown marker"
                color = (255, 0, 0)

            current_time = time.time()

            if marker_name not in last_detected_time or (
                    current_time - last_detected_time[marker_name]) > marker_cooldown:
                last_detected_time[marker_name] = current_time
                marker_results.append(
                    (second_largest_circle[0], second_largest_circle[1], unique_inner_counts, marker_name,
                     second_largest_circle[5], color, distance))
                detected_markers = True
                frames_with_marker += 1

                if not previous_detected or (previous_marker != marker_name):
                    angle = calculate_angle(frame.shape[1], second_largest_circle[0])
                    direction = angle_to_direction(angle)
                    print(
                        f"{marker_name} at ({round(second_largest_circle[0])}, {round(second_largest_circle[1])}), Distance: {distance},"
                        f"{steps}, Angle: {angle:.2f} degrees, Direction: {direction}")
                    update_flask_data(marker_name, steps, direction)

                previous_marker = marker_name
                previous_detected = True
            else:
                previous_detected = False

    frames_processed += 1

    return frame, detected_markers



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

            # Wykrywanie markerow
            output_image, found_marker = detect_markers(color_image, depth_frame)
            # Wykrywanie ludzi
            output_image, _ = detect_objects(people_model, output_image)
            # Wykrywanie klamek
            output_image, _ = detect_objects(doorknob_model, output_image)
            cv2.imshow('Detection', output_image)

            #if found_marker:
             #   print(f"Marker found. Paused. Detected on {frames_with_marker} out of {frames_processed} frames.")

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
            if paused:
                print(f"Paused. Detected on {frames_with_marker} out of {frames_processed} frames.")
            else:
                print("Resumed")

finally:
    pipeline.stop()
    cv2.destroyAllWindows()