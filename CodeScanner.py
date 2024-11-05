import pyrealsense2 as rs
import numpy as np
import cv2
import socket

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

def send_data_to_pi(data):
    IP = ""
    PORT = 8000
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((IP, PORT))
            s.sendall(data.encode())
    except Exception as e:
        print(f"Failed to send data: {e}")


def detect_custom_marker(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20,
                               param1=50, param2=30, minRadius=10, maxRadius=100)

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        circles = sorted(circles, key=lambda x: x[2], reverse=True)

        if len(circles) >= 3:
            inner_circle, middle_circle, outer_circle = circles[:3]

            if validate_marker(inner_circle, middle_circle, outer_circle):
                return inner_circle, middle_circle, outer_circle
    return None


def validate_marker(inner, middle, outer):
    radius_ratio_threshold = 0.5
    distance_ratio_threshold = 0.2

    inner_radius = inner[2]
    middle_radius = middle[2]
    outer_radius = outer[2]

    if (middle_radius / inner_radius > radius_ratio_threshold) and (
            outer_radius / middle_radius > radius_ratio_threshold):
        return True
    return False