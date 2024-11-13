import cv2
import pyrealsense2 as rs
import numpy as np

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
pipeline.start(config)

object_dict = {1: "Object 1", 2: "Object 2", 3: "Object 3", 4: "Object 4"}

paused = False


def detect_markers(frame, depth_frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    cv2.imshow("Binary Frame", binary)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    markers = []
    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area < 1000 or area > 10000:
            continue

        if len(cnt) >= 5:
            ellipse = cv2.fitEllipse(cnt)
            (x, y), (MA, ma), angle = ellipse
            circularity = min(MA, ma) / max(MA, ma)

            if circularity >= 0.8:
                markers.append((x, y, MA, ma, cnt, ellipse))

    concentric_markers = []
    for i, (x1, y1, MA1, ma1, cnt1, ellipse1) in enumerate(markers):
        for j, (x2, y2, MA2, ma2, cnt2, ellipse2) in enumerate(markers):
            if i != j and MA1 > MA2:
                dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                if dist < MA1 / 4:
                    concentric_markers.append((x1, y1, MA1, ma1, cnt1, cnt2, ellipse1))

    for x, y, MA, ma, outer_cnt, inner_cnt, outer_ellipse in concentric_markers:
        inner_circles = [
            c for c in contours
            if cv2.contourArea(c) < cv2.contourArea(outer_cnt) / 4
               and cv2.pointPolygonTest(outer_cnt, (int(c[0][0][0]), int(c[0][0][1])), False) >= 0
        ]
        inner_count = len(inner_circles)

        object_name = object_dict.get(inner_count, "Unknown object")

        h, w = frame.shape[:2]
        if 0 <= int(x) < w and 0 <= int(y) < h:
            depth_value = depth_frame.get_distance(int(x), int(y))
            distance = depth_value if depth_value != 0 else "Unknown"

            direction = "center"
            if x < w // 3:
                direction = "left"
            elif x > 2 * w // 3:
                direction = "right"

            print(f"{object_name}, Distance: {distance}m, Direction: {direction}")

            cv2.ellipse(frame, outer_ellipse, (0, 255, 0), 2)
            cv2.putText(frame, f"Marker {inner_count}", (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 0), 2)
            cv2.drawContours(frame, [inner_cnt], -1, (255, 0, 0), 2)
            for c in inner_circles:
                cv2.drawContours(frame, [c], -1, (255, 255, 0), 2)

    return frame


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

            output_image = detect_markers(color_image, depth_frame)

            cv2.imshow('Marker Detection', output_image)

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