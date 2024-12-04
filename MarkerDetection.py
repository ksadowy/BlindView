import cv2
import pyrealsense2 as rs
import numpy as np
import time

# Inicjalizacja kamery RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
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


def calculate_angle(width, x):
    """
    Przekształca współrzędne x obrazu na kąt
    pomiędzy -90 a 90 stopni, gdzie -90 to lewo,
    a 90 to prawo
    :param width: szerokość obrazu
    :param x: współrzędna x
    :return: kąt w stopniach (-90, 90)
    """

    # Odchylenie od środka obrazu -> przekształcenie na kąt
    deviation = x - width / 2
    angle = (deviation / (width / 2)) * 90

    return angle

def angle_to_direction(angle):
    """
    Przekształca kąt na kierunek w godzinach zgodnie ze wskazówkami zegara
    :param angle: kąt w stopniach (-90, 90)
    :return: kierunek w godzinach
    """

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
    """
    Sprawdza, czy dwa okręgi są duplikatami na podstawie bliskości centrów i podobieństwa rozmiarów.
    """
    (x1, y1, MA1, ma1, _, _, _, _, _) = circle1
    (x2, y2, MA2, ma2, _, _, _, _, _) = circle2

    # Porównanie centrów
    center_distance = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    if center_distance > center_tolerance:
        return False

    # Porównanie rozmiarów (średnia długość osi elipsy)
    size1 = (MA1 + ma1) / 2
    size2 = (MA2 + ma2) / 2
    if abs(size1 - size2) / size1 > size_tolerance:
        return False

    return True


def detect_markers(frame, depth_frame):
    global previous_marker, previous_detected

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    blurred = cv2.GaussianBlur(blurred, (5, 5), 0)
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2
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

        # Filtracja konturów o zbyt małej powierzchni i obwodzie
        if area < 200 or perimeter < 50:
            continue

        circularity = 4 * np.pi * area / (perimeter ** 2)

        if circularity > 0.7:
            try:
                ellipse = cv2.fitEllipse(cnt)
                (x, y), (MA, ma), _ = ellipse
                circularity_ellipse = min(MA, ma) / max(MA, ma)

                # Filtracja elips o zbyt krótkich półosiach
                if min(MA, ma) < 15 or max(MA, ma) < 15:
                    continue

                if 0.8 <= circularity_ellipse <= 1.2:
                    valid_circles.append((x, y, MA, ma, cnt, ellipse, hierarchy[0][i], area, perimeter))
            except cv2.error as e:
                print("Error fitting ellipse: ", e)
                continue

    # Filtrowanie duplikatów
    filtered_circles = []
    for circle in valid_circles:
        is_duplicate_circle = any(is_duplicate(circle, existing_circle) for existing_circle in filtered_circles)
        if not is_duplicate_circle:
            filtered_circles.append(circle)

    valid_circles = filtered_circles

    # Sortowanie okręgów wg wielkości
    valid_circles.sort(key=lambda c: c[2] * c[3], reverse=True)

    detected_markers = False
    marker_results = []
    second_largest_circle = None  # Inicjalizacja zmiennej

    # Zaznaczenie największego i drugiego największego okręgu
    for idx, circle in enumerate(valid_circles):
        id_label = f"ID: {idx}"
        if idx == 0:
            cv2.ellipse(frame, circle[5], (255, 0, 0), 2)  # Największy okrąg na niebiesko
            cv2.putText(frame, id_label, (int(circle[0]), int(circle[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0),
                        2)
        elif idx == 1:
            second_largest_circle = circle  # Przypisanie wartości
            cv2.ellipse(frame, circle[5], (0, 0, 255), 2)  # Drugi największy okrąg na czerwono
            cv2.putText(frame, id_label, (int(circle[0]), int(circle[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255),
                        2)
        else:
            cv2.ellipse(frame, circle[5], (0, 255, 0), 2)  # Pozostałe mniejsze okręgi na zielono
            cv2.putText(frame, id_label, (int(circle[0]), int(circle[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                        2)

    if second_largest_circle:
        depth_value = depth_frame.get_distance(int(second_largest_circle[0]), int(second_largest_circle[1]))
        distance = f"{depth_value:.2f}m" if depth_value != 0 else "Unknown"
        steps = f"{round(depth_value * 1.31)} steps" if depth_value != 0 else "Unknown"

        if depth_value <= 5:  # Odrzucenie zakłóceń z dużym dystansem
            unique_inner_counts = len(valid_circles) // 2  # Dzielenie na 2, aby uniknąć duplikatów

            if unique_inner_counts in marker_dict:
                marker_name = marker_dict[unique_inner_counts]
                color = (0, 255, 0)
            else:
                marker_name = "Unknown marker"
                color = (255, 0, 0)

            current_time = time.time()

            # Sprawdzenie cooldownu
            if marker_name not in last_detected_time or (
                    current_time - last_detected_time[marker_name]) > marker_cooldown:
                last_detected_time[marker_name] = current_time
                marker_results.append(
                    (second_largest_circle[0], second_largest_circle[1], unique_inner_counts, marker_name,
                     second_largest_circle[5], color, distance))
                detected_markers = True

                if not previous_detected or (previous_marker != marker_name):
                    angle = calculate_angle(frame.shape[1], second_largest_circle[0])
                    direction = angle_to_direction(angle)
                    print(
                        f"{marker_name} at ({round(second_largest_circle[0])}, {round(second_largest_circle[1])}), Distance: {distance},"
                        f"{steps} - {unique_inner_counts} circles, Angle: {angle:.2f} degrees, Direction: {direction}")

                previous_marker = marker_name
                previous_detected = True
            else:
                previous_detected = False

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

            output_image, found_marker = detect_markers(color_image, depth_frame)
            cv2.imshow('Marker Detection', output_image)

            if found_marker:
                paused = True  # Pauza po wykryciu markera
                print("Marker found. Paused")

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
            if paused:
                print("Paused")
            else:
                print("Resumed")

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
