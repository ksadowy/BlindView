import pyrealsense2 as rs
import numpy as np
import cv2
from pyzbar import pyzbar

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

pipeline.start(config)

try:
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        hsv_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)

        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        red_mask = cv2.inRange(hsv_image, lower_red, upper_red)

        red_qr_image = cv2.bitwise_and(color_image, color_image, mask=red_mask)
        gray_red_qr = cv2.cvtColor(red_qr_image, cv2.COLOR_BGR2GRAY)
        inverted_gray_red_qr = cv2.bitwise_not(gray_red_qr)
        cv2.imshow("QR Code", inverted_gray_red_qr)

        qr_codes = pyzbar.decode(inverted_gray_red_qr)

        for qr_code in qr_codes:
            x, y, w, h = qr_code.rect
            if w < 50 or h < 50:
                continue

            qr_data = qr_code.data.decode("utf-8")
            object_name = qr_data

            center_x = x + w // 2
            center_y = y + h // 2

            depth = depth_frame.get_distance(center_x, center_y)

            depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
            point_3d = rs.rs2_deproject_pixel_to_point(depth_intrin, [center_x, center_y], depth)

            distance = np.linalg.norm(point_3d)
            direction = (np.arctan2(point_3d[0], point_3d[2]), np.arctan2(point_3d[1], point_3d[2]))

            cv2.rectangle(color_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(color_image, object_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            if direction[0] > 1:
                direction = "right"
            elif direction[0] < -1:
                direction = "left"
            else:
                direction = "ahead"

            print(f"Object: {object_name}")
            print(f"Distance to Object: {distance:.2f} meters")
            print(f"Direction: {direction}")

        # Display the color image with bounding boxes
        cv2.imshow('RealSense', color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
