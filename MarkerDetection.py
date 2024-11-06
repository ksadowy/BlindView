import cv2
import pyrealsense2 as rs
import numpy as np

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

# Dict z obiektami, ktore potencjalnie mozna wykryc
object_dict = {1: "Object 1", 2: "Object 2", 3: "Object 3", 4: "Object 4"}


def detect_markers(frame, depth_frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # Kontury
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    circles = []

    # Filtr, aby zachowac tylko te zblizone do ksztaltu okregu
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500 or area > 5000:
            continue

        if len(cnt) >= 5:
            ellipse = cv2.fitEllipse(cnt)
            (x, y), (MA, ma), angle = ellipse
            circularity = min(MA, ma) / max(MA, ma)

            if circularity >= 0.8:
                circles.append((x, y, MA, ma, cnt, ellipse))

    # Podwojne okregi
    markers = []
    for i, (x1, y1, MA1, ma1, cnt1, ellipse1) in enumerate(circles):
        for j, (x2, y2, MA2, ma2, cnt2, ellipse2) in enumerate(circles):
            if i != j and MA1 > MA2:
                dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                if dist < MA1 / 2:
                    markers.append((x1, y1, MA1, ma1, cnt1, ellipse1, cnt2))

    for x, y, MA, ma, outer_cnt, outer_ellipse, inner_cnt in markers:
        ratio = MA / ma
        if not (0.75 <= ratio <= 1.25):
            continue

        # Liczenie mniejszych okregow
        inner_circles = [
            c for c in contours if cv2.contourArea(c) < cv2.contourArea(outer_cnt) / 4
        ]
        inner_count = len(inner_circles)

        # Domyslnie nieznany obiekt
        object_name = object_dict.get(inner_count, "Unknown object")

        h, w = frame.shape[:2]
        if 0 <= int(x) < w and 0 <= int(y) < h:
            depth_value = depth_frame.get_distance(int(x), int(y))
            distance = depth_value if depth_value != 0 else "Unknown"

            # Kierunek do wykrytego obiektu
            direction = "center"
            if x < w // 3:
                direction = "left"
            elif x > 2 * w // 3:
                direction = "right"

            print(f"{object_name}, Distance: {distance} m, Direction: {direction}")

            # Rysowanie markerow
            cv2.ellipse(frame, outer_ellipse, (0, 255, 0), 2)
            cv2.drawContours(frame, [inner_cnt], -1, (255, 0, 0), 2)
            for c in inner_circles:
                cv2.drawContours(frame, [c], -1, (255, 255, 0), 2)

    return frame


try:
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        output_image = detect_markers(color_image, depth_frame)

        cv2.imshow('Marker Detection', output_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
