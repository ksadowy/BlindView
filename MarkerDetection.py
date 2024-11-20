import cv2
import pyrealsense2 as rs
import numpy as np

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
    4: "Marker 4",
    5: "Marker 5"
}

# Metry na kroki
def meters_to_steps(distance):
    return round(distance * 1.31)


def detect_markers(frame, depth_frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
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
                    valid_circles.append((x, y, MA, ma, cnt, ellipse, hierarchy[0][i]))
            except cv2.error as e:
                print("Error fitting ellipse: ", e)
                continue

    detected_markers = False
    marker_results = []

    # Sortowanie okręgów wg wielkości (największy najpierw)
    valid_circles.sort(key=lambda c: c[2] * c[3], reverse=True)

    # Ignorowanie największego okręgu
    if valid_circles:
        valid_circles.pop(0)  # Usunięcie największego okręgu z listy

    # Zaznaczenie drugiego największego okręgu na czerwono (teraz największego na liście)
    if valid_circles:
        second_largest_circle = valid_circles.pop(0)
        cv2.ellipse(frame, second_largest_circle[5], (0, 0, 255), 2)

    # Zaznaczenie pozostałych mniejszych okręgów na zielono
    for circle in valid_circles:
        cv2.ellipse(frame, circle[5], (0, 255, 0), 2)

    # Zakładam, że detekcja odległości i markerów, bazuje na drugim największym okręgu
    if 'second_largest_circle' in locals():
        depth_value = depth_frame.get_distance(int(second_largest_circle[0]), int(second_largest_circle[1]))
        distance = f"{depth_value:.2f}m" if depth_value != 0 else "Unknown"

        if depth_value <= 5:  # Odrzucenie zakłóceń z dużym dystansem
            unique_inner_counts = len(valid_circles) // 2  # Dzielenie na 2, aby uniknąć duplikatów

            if unique_inner_counts in marker_dict:
                marker_name = marker_dict[unique_inner_counts]
                color = (0, 255, 0)
            else:
                marker_name = "Unknown marker"
                color = (255, 0, 0)

            marker_results.append((second_largest_circle[0], second_largest_circle[1], unique_inner_counts, marker_name,
                                   second_largest_circle[5], color, distance))

            detected_markers = True

    for x, y, inner_count, marker_name, ellipse, color, distance in marker_results:
        cv2.putText(frame, marker_name, (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        print(f"{marker_name} at ({round(x)}, {round(y)}), Distance: {distance}, {meters_to_steps(depth_value)} steps - {inner_count} inner circles")

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
