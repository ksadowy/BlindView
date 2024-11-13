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

    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours is None or hierarchy is None:
        return frame, False

    valid_circles = []
    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)

        if perimeter == 0:
            continue

        circularity = 4 * np.pi * area / (perimeter ** 2)

        if 500 < area < 20000 and circularity > 0.7:
            try:
                ellipse = cv2.fitEllipse(cnt)
                (x, y), (MA, ma), _ = ellipse
                circularity_ellipse = min(MA, ma) / max(MA, ma)

                if 0.8 <= circularity_ellipse <= 1.2:
                    valid_circles.append((x, y, MA, ma, cnt, ellipse, hierarchy[0][i]))
            except cv2.error as e:
                print("Error fitting ellipse: ", e)
                continue

    detected_markers = False
    marker_results = []

    outer_circles = [circle for circle in valid_circles if circle[6][3] == -1]

    for oc in outer_circles:
        x, y, MA, ma, outer_cnt, ellipse, hier = oc
        mask = np.zeros_like(binary)
        cv2.drawContours(mask, [outer_cnt], -1, 255, -1)

        inner_circles = []
        for ix, ic in enumerate(valid_circles):
            if cv2.pointPolygonTest(outer_cnt, (ic[0], ic[1]), False) >= 0 and ix != outer_circles.index(oc):
                inner_circles.append(ic)

        if inner_circles:
            inner_count = len(inner_circles)
            depth_value = depth_frame.get_distance(int(x), int(y))
            distance = f"{depth_value:.2f}m" if depth_value != 0 else "Unknown"

            if inner_count in marker_dict:
                marker_name = marker_dict[inner_count]
                color = (0, 0, 255)
                detected_markers = True
            else:
                marker_name = "Unknown marker"
                color = (255, 0, 0)

            if depth_value > 5:  # Odrzucenie zakłóceń z dużym dystansem
                continue

            for inner_circle in inner_circles:
                cX, cY, _, _, _, inner_ellipse, _ = inner_circle
                cv2.circle(frame, (int(cX), int(cY)), 5, (0, 255, 0), -1)
                cv2.ellipse(frame, inner_ellipse, (255, 0, 0), 2)  # Możesz zmienić kolor dla wewnętrznych

            marker_results.append((x, y, inner_count, marker_name, ellipse, inner_circles, color, distance))

    for x, y, inner_count, marker_name, ellipse, inner_circles, color, distance in marker_results:
        cv2.ellipse(frame, ellipse, color, 2)

        print(f"{marker_name} with {inner_count} inner circles at ({round(x)}, {round(y)}), Distance: {distance}")
        if marker_name != "Unknown marker":
            cv2.putText(frame, f"{marker_name}", (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 0), 2)  # Tekst w kolorze zielonym

    return frame, any([r[2] > 0 for r in marker_results])


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
