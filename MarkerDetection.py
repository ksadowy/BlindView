import cv2
import pyrealsense2 as rs
import numpy as np
import time

from fontTools.ttx import process
from ultralytics import YOLO
import requests

# Global variables and constants
processing_lock = None
MIN_OBJECT_DISTANCE = 1.0
MIN_MARKER_DISTANCE = 0.5

# YOLO models - people and doorknobs detection
people_model = YOLO("ludzie.pt")
doorknob_model = YOLO("klamki.pt")

# RealSense camera configuration
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 15)
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 15)
pipeline.start(config)

paused = False

marker_dict = {
    1: "Krzesło", # Marker 1
    2: "Ławka", # Marker 2
    3: "Biurko", # Marker 3
    4: "Szafa", # Marker 4
    5: "Kosz na śmieci" # Marker 5
}


# Cooldowns for marker and YOLO detections
marker_cooldown = 10
yolo_cooldown = 10
last_detected_time = {}

# Previous marker and detection flag
previous_marker = None
previous_detected = False

frames_processed = 0
frames_with_marker = 0


def calculate_angle(width, x):
    """
    Calculate the angle of deviation from the center of the image.
    :param width: Width of the image in pixels.
    :param x: X-coordinate of the point to calculate the angle for.
    :return: Angle of deviation in degrees.
    """
    deviation = x - width / 2
    angle = (deviation / (width / 2)) * 90
    return angle


def angle_to_direction(angle):
    """
    Convert an angle to a clock direction.
    :param angle: Angle in degrees.
    :return: String representing the clock direction.
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


def update_flask_data(new_marker_name, new_steps, new_direction):
    """
    Send data to the Flask server.
    :param new_marker_name: Name of the detected marker.
    :param new_steps: Distance to the marker in steps.
    :param new_direction: Direction of the marker.
    :return: None
    """
    url = "http://127.0.0.1:5000/api/update"
    payload = {
        "marker_name": new_marker_name,
        "steps": new_steps,
        "direction": new_direction
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("API updated")
        else:
            print("Error during updating flask's API")
    except Exception as e:
        print(f"Connection error: {e}")



def is_duplicate(circle1, circle2, center_tolerance=15, size_tolerance=0.15):
    """
    Check if two circles are duplicates based on their centers and sizes.
    :param circle1: Tuple containing circle1's properties (x, y, MA, ma, ...).
    :param circle2: Tuple containing circle2's properties (x, y, MA, ma, ...).
    :param center_tolerance: Maximum allowed distance between centers in pixels.
    :param size_tolerance: Maximum allowed size difference as a ratio.
    :return: True if the circles are duplicate, otherwise False.
    """
    (x1, y1, MA1, ma1, _, _, _, _, _) = circle1
    (x2, y2, MA2, ma2, _, _, _, _, _) = circle2

    center_distance = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    if center_distance > center_tolerance:
        return False

    size1 = (MA1 + ma1) / 2
    size2 = (MA2 + ma2) / 2
    if abs(size1 - size2) / size1 > size_tolerance:
        return False

    return True


def detect_inner_circles(binary_image):
    """
    Detect inner circles in a binary image using the Hough Circle Transform.
    :param binary_image: Binary image to detect circles in.
    :return: List of detected circles, each represented as (x, y, radius).
    """
    detected_circles = cv2.HoughCircles(
        binary_image,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=10,
        param1=50,
        param2=30,
        minRadius=5,
        maxRadius=30
    )

    if detected_circles is not None:
        detected_circles = np.uint16(np.around(detected_circles))
        return detected_circles[0, :]
    return []


def detect_objects(model, frame, depth_frame):
    """
    Detect objects in a frame using YOLO model.
    :param model: YOLO model to use for detection.
    :param frame: Color frame to detect objects in.
    :param depth_frame: Depth frame to calculate distances.
    :return: Tuple containing the processed frame and a list of detections.
    """
    global processing_lock, last_detected_time, yolo_cooldown

    if processing_lock is not None and processing_lock != "objects":
        return frame, []

    processing_lock = "objects"

    # Detect objects using YOLO
    results = model.predict(source=frame, conf=0.5, iou=0.5, classes=None, device="cpu")
    detections = results[0].boxes.xyxy.cpu().numpy() # Bounding box coordinates
    confidences = results[0].boxes.conf.cpu().numpy() # Confidence scores
    class_ids = results[0].boxes.cls.cpu().numpy() # Class IDs

    for (box, confidence, class_id) in zip(detections, confidences, class_ids):
        x1, y1, x2, y2 = map(int, box)
        label = f"ID: {int(class_id)} ({confidence:.2f})"
        color = (0, 255, 0) if model == people_model else (255, 0, 0)  # Color depends on the model
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Calculate the center of the object
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        # Get depth value
        depth_value = depth_frame.get_distance(center_x, center_y)
        distance = f"{depth_value:.2f}m" if depth_value != 0 else "Unknown"
        steps = f"{round(depth_value * 1.31)} steps" if depth_value != 0 else "Unknown"

        if depth_value < MIN_OBJECT_DISTANCE:
            continue

        # Calculate time and direction
        angle = calculate_angle(frame.shape[1], center_x)
        direction = angle_to_direction(angle)

        object_name = "Człowiek" if model == people_model else "Klamka"

        # Check cooldown
        current_time = time.time()
        if object_name not in last_detected_time or (current_time - last_detected_time[object_name]) > yolo_cooldown:
            last_detected_time[object_name] = current_time

            print(
                f"{object_name} detected at ({center_x}, {center_y}), Distance: {distance}, "
                f"{steps}, Angle: {angle:.2f} degrees, Direction: {direction}"
            )

            update_flask_data(object_name, steps, direction)

    processing_lock = None
    return frame, detections



def detect_markers(frame, depth_frame):
    """
    Detect markers in the frame based on circular patterns and inner circles.
    :param frame: Color frame to detect markers in.
    :param depth_frame: Depth frame to calculate distances.
    :return: Tuple containing the processed frame and a boolean indicating if a marker was detected.
    """
    global processing_lock, previous_marker, previous_detected, frames_processed, frames_with_marker

    if processing_lock is not None and processing_lock != "markers":
        return frame, False

    processing_lock = "markers"

    # Image processing
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 5)
    blurred = cv2.GaussianBlur(blurred, (5, 5), 0)
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        13,
        3
    )

    cv2.imshow("Binary Frame", binary)

    # Detect contours
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours is None or hierarchy is None:
        return frame, False

    # Filter contours
    valid_circles = []
    for i, cnt in enumerate(contours):
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        area = cv2.contourArea(cnt)

        if area < 350 or perimeter < 70:
            continue

        circularity = 4 * np.pi * area / (perimeter ** 2)

        if circularity > 0.7:
            try:
                ellipse = cv2.fitEllipse(cnt)
                (x, y), (MA, ma), _ = ellipse
                circularity_ellipse = min(MA, ma) / max(MA, ma)

                if min(MA, ma) < 10 or max(MA, ma) < 50:
                    continue

                if 0.8 <= circularity_ellipse <= 1.2:
                    valid_circles.append((x, y, MA, ma, cnt, ellipse, hierarchy[0][i], area, perimeter))
            except cv2.error as e:
                print("Error fitting ellipse: ", e)
                continue

    # Filter duplicates
    filtered_circles = []
    for circle in valid_circles:
        is_duplicate_circle = any(is_duplicate(circle, existing_circle) for existing_circle in filtered_circles)
        if not is_duplicate_circle:
            filtered_circles.append(circle)

    valid_circles = filtered_circles

    # Sort circles by size
    valid_circles.sort(key=lambda c: c[2] * c[3], reverse=True)

    detected_markers = False
    marker_results = []
    second_largest_circle = None

    # Draw circles and detect markers
    for idx, circle in enumerate(valid_circles):
        id_label = f"ID: {idx}"
        if idx == 0:
            cv2.ellipse(frame, circle[5], (255, 0, 0), 2)
            cv2.putText(frame, id_label, (int(circle[0]), int(circle[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0),
                        2)
        elif idx == 1:
            second_largest_circle = circle
            cv2.ellipse(frame, circle[5], (0, 0, 255), 2)
            cv2.putText(frame, id_label, (int(circle[0]), int(circle[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255),
                        2)

            # Detect inner circles
            x_start = max(0, int(circle[0] - circle[2] / 2))
            x_end = min(binary.shape[1], int(circle[0] + circle[2] / 2))
            y_start = max(0, int(circle[1] - circle[3] / 2))
            y_end = min(binary.shape[0], int(circle[1] + circle[3] / 2))

            roi = binary[y_start:y_end, x_start:x_end]

            cv2.rectangle(frame, (x_start, y_start), (x_end, y_end), (255, 255, 0), 2)

            inner_circles = detect_inner_circles(roi)
            if inner_circles is not None:
                for inner_circle in inner_circles:
                    offset_x = x_start
                    offset_y = y_start
                    cv2.circle(frame, (inner_circle[0] + offset_x, inner_circle[1] + offset_y), inner_circle[2],
                               (0, 255, 255), 2)

        else:
            cv2.ellipse(frame, circle[5], (0, 255, 0), 2)
            cv2.putText(frame, id_label, (int(circle[0]), int(circle[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                        2)

    # Detect markers based on inner circles
    if second_largest_circle:
        depth_value = depth_frame.get_distance(int(second_largest_circle[0]), int(second_largest_circle[1]))
        distance = f"{depth_value:.2f}m" if depth_value != 0 else "Unknown"
        steps = f"{round(depth_value * 1.31)} steps" if depth_value != 0 else "Unknown"

        if depth_value < MIN_MARKER_DISTANCE:
            return frame, False

        if depth_value <= 5:
            unique_inner_counts = len(inner_circles)

            if unique_inner_counts in marker_dict:
                marker_name = marker_dict[unique_inner_counts]
                color = (0, 255, 0)
            else:
                marker_name = "Unknown marker"
                color = (255, 0, 0)

            current_time = time.time()

            if marker_name not in last_detected_time or (
                    current_time - last_detected_time[marker_name]) > marker_cooldown:
                last_detected_time[marker_name] = current_time
                marker_results.append(
                    (second_largest_circle[0], second_largest_circle[1], unique_inner_counts, marker_name,
                     second_largest_circle[5], color, distance))
                detected_markers = True
                frames_with_marker += 1

                if not previous_detected or (previous_marker != marker_name):
                    angle = calculate_angle(frame.shape[1], second_largest_circle[0])
                    direction = angle_to_direction(angle)
                    print(
                        f"{marker_name} at ({round(second_largest_circle[0])}, {round(second_largest_circle[1])}), Distance: {distance},"
                        f"{steps}, Angle: {angle:.2f} degrees, Direction: {direction}")
                    update_flask_data(marker_name, steps, direction)

                previous_marker = marker_name
                previous_detected = True
            else:
                previous_detected = False

    frames_processed += 1

    processing_lock = None
    return frame, detected_markers



try:
    while True:
        if not paused:
            # Get frames from the camera
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            # Detect markers and objects
            output_image, found_marker = detect_markers(color_image, depth_frame)
            output_image, _ = detect_objects(people_model, output_image, depth_frame)
            output_image, _ = detect_objects(doorknob_model, output_image, depth_frame)
            cv2.imshow('Detection', output_image)

            #if found_marker:
             #   print(f"Marker found. Paused. Detected on {frames_with_marker} out of {frames_processed} frames.")

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
            if paused:
                print(f"Paused. Detected on {frames_with_marker} out of {frames_processed} frames.")
            else:
                print("Resumed")

finally:
    # Stop the camera and close windows
    pipeline.stop()
    cv2.destroyAllWindows()