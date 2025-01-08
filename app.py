from flask import Flask, jsonify
import cv2
import pyrealsense2 as rs
import numpy as np
import time

app = Flask(__name__)

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
pipeline.start(config)

marker_dict = {
    1: "Marker 1",
    2: "Marker 2",
    3: "Marker 3",
    4: "Marker 4"
}
marker_cooldown = 10
last_detected_time = {}


def calculate_angle(width, x):
    deviation = x - width / 2
    angle = (deviation / (width / 2)) * 90
    return angle


def angle_to_direction(angle):
    if -90 <= angle < -75:
        return "9 o'clock"
    elif -75 <= angle < -45:
        return "10 o'clock"
    elif -45 <= angle < -15:
        return "11 o'clock"
    elif -15 <= angle <= 15:
        return "12 o'clock"
    elif 15 < angle <= 45:
        return "1 o'clock"
    elif 45 < angle <= 75:
        return "2 o'clock"
    elif 75 < angle <= 90:
        return "3 o'clock"
    else:
        return "Unknown"


def detect_markers():
    frames = pipeline.wait_for_frames()
    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()

    if not depth_frame or not color_frame:
        return None

    color_image = np.asanyarray(color_frame.get_data())
    gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
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
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours is None or hierarchy is None:
        return None

    valid_circles = []
    for i, cnt in enumerate(contours):
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        area = cv2.contourArea(cnt)
        if area < 200 or perimeter < 50:
            continue

        circularity = 4 * np.pi * area / (perimeter ** 2)
        if circularity > 0.7:
            try:
                ellipse = cv2.fitEllipse(cnt)
                (x, y), (MA, ma), _ = ellipse
                circularity_ellipse = min(MA, ma) / max(MA, ma)
                if min(MA, ma) < 15 or max(MA, ma) < 15:
                    continue
                if 0.8 <= circularity_ellipse <= 1.2:
                    valid_circles.append((x, y, MA, ma, cnt, ellipse, hierarchy[0][i], area, perimeter))
            except cv2.error:
                continue

    valid_circles.sort(key=lambda c: c[2] * c[3], reverse=True)
    if len(valid_circles) < 2:
        return None

    second_largest_circle = valid_circles[1]
    depth_value = depth_frame.get_distance(int(second_largest_circle[0]), int(second_largest_circle[1]))
    if depth_value <= 5:
        unique_inner_counts = len(valid_circles) // 2
        if unique_inner_counts in marker_dict:
            marker_name = marker_dict[unique_inner_counts]
            angle = calculate_angle(color_image.shape[1], second_largest_circle[0])
            direction = angle_to_direction(angle)
            return {
                "marker_name": marker_name,
                "coordinates": (round(second_largest_circle[0]), round(second_largest_circle[1])),
                "distance": f"{depth_value:.2f}m",
                "direction": direction
            }

    return None


@app.route('/get_marker_info', methods=['GET'])
def get_marker_info():
    marker_info = detect_markers()
    if marker_info:
        return jsonify(marker_info)
    else:
        return jsonify({"message": "No marker detected."})


if __name__ == "__main__":
    app.run(debug=True)