import pyrealsense2 as rs
import numpy as np
import cv2

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

marker_dict = {1: "a", 2: "b", 3: "c", 4: "d"}

# Start streaming
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
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        circles = cv2.HoughCircles(
            gray_image, cv2.HOUGH_GRADIENT, dp=1.2, minDist=30,
            param1=50, param2=30, minRadius=10, maxRadius=100
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))

            large_circles = []
            small_circles = []

            for circle in circles[0, :]:
                x, y, radius = circle
                if 80 <= radius <= 100:
                    large_circles.append((x, y, radius))
                elif 10 <= radius < 30:
                    small_circles.append((x, y, radius))

            for (lx, ly, lr) in large_circles:
                inner_count = 0

                for (sx, sy, sr) in small_circles:
                    distance_to_large_center = np.sqrt((lx - sx) ** 2 + (ly - sy) ** 2)
                    if distance_to_large_center < lr:
                        inner_count += 1

                marker_type = marker_dict.get(inner_count, "Unknown")

                depth = depth_frame.get_distance(lx, ly)
                depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
                point_3d = rs.rs2_deproject_pixel_to_point(depth_intrin, [lx, ly], depth)

                distance = np.linalg.norm(point_3d)
                azimuth = np.arctan2(point_3d[0], point_3d[2])
                elevation = np.arctan2(point_3d[1], point_3d[2])

                cv2.circle(color_image, (lx, ly), lr, (0, 255, 0), 2)  # Draw large circle
                cv2.putText(color_image, f"Marker: {marker_type}", (lx - 40, ly - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                print(f"Marker: {marker_type}")
                print(f"Distance to Marker: {distance:.2f} meters")
                if azimuth > 1:
                    direction = "right"
                elif azimuth < -1:
                    direction = "left"
                else:
                    direction = "ahead"
                print(f"Direction: {direction}")

        cv2.imshow('RealSense', color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
