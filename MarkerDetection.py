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
    4: "Marker 4"
}


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

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    large_circles = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 500 < area < 20000:
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter ** 2)

            if circularity > 0.7:
                ellipse = cv2.fitEllipse(cnt)
                (x, y), (MA, ma), angle = ellipse
                circularity_ellipse = min(MA, ma) / max(MA, ma)

                if 0.8 <= circularity_ellipse <= 1.2:
                    large_circles.append((x, y, MA, ma, cnt, ellipse))

    if len(large_circles) >= 2:
        largest_circles = sorted(large_circles, key=lambda x: max(x[2], x[3]), reverse=True)[:2]
        for i, (_, _, _, _, cnt, ellipse) in enumerate(largest_circles):
            color = (0, 0, 255) if i == 0 else (255, 0, 0)
            cv2.ellipse(frame, ellipse, color, 2)
            cv2.drawContours(frame, [cnt], -1, color, 2)

    min_inner_area_factor = 1 / 100
    max_inner_area_factor = 1 / 10

    detected_markers = False
    for i, (_, _, _, _, outer_cnt, outer_ellipse) in enumerate(large_circles):
        outer_area = cv2.contourArea(outer_cnt)
        min_inner_area = outer_area * min_inner_area_factor
        max_inner_area = outer_area * max_inner_area_factor

        inner_circles = []
        for c in contours:
            if min_inner_area < cv2.contourArea(c) < max_inner_area:
                M = cv2.moments(c)
                if M["m00"] == 0:
                    continue
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                if cv2.pointPolygonTest(outer_cnt, (cX, cY), False) > 0:
                    inner_circles.append(c)
                    cv2.drawContours(frame, [c], -1, (0, 255, 0), 2)  # Zielony dla wewnętrznych okręgów

        if i < 2:
            inner_count = len(inner_circles)
            marker_name = marker_dict.get(inner_count, "Unknown marker")

            frame_h, frame_w = frame.shape[:2]
            direction = "center"
            (x, y) = (int(outer_ellipse[0][0]), int(outer_ellipse[0][1]))
            if x < frame_w // 3:
                direction = "left"
            elif x > 2 * frame_w // 3:
                direction = "right"

            depth_value = depth_frame.get_distance(int(x), int(y))
            if depth_value != 0:
                distance = f"{depth_value:.2f}m"
            else:
                distance = "Unknown"

            direction_hours = "unknown"
            if direction == "left":
                direction_hours = "9 o'clock"
            elif direction == "right":
                direction_hours = "3 o'clock"
            elif direction == "center":
                direction_hours = "12 o'clock"

            print(f"{marker_name} with {inner_count} inner circles, Direction: {direction_hours}, Distance: {distance}")

            cv2.putText(frame, f"Marker {inner_count}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 0), 2)  # Tekst w kolorze zielonym

            detected_markers = True

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
                print("Paused for inspection.")

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