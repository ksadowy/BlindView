import pyrealsense2 as rs
import numpy as np
import cv2

net = cv2.dnn.readNet("yolov3-tiny.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

classes = ["person"]
relevant_class_ids = [0]

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)

pipeline.start(config)

def get_direction(center_x, img_width):
    if center_x < img_width / 3:
        return "Left"
    elif center_x > 2 * img_width / 3:
        return "Right"
    else:
        return "Center"

try:
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())

        blob = cv2.dnn.blobFromImage(color_image, 1 / 255.0, (416, 416), (0, 0, 0), swapRB=True, crop=False)
        net.setInput(blob)

        detections = net.forward(output_layers)

        height, width, _ = color_image.shape
        found_person = False

        for output in detections:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                print(f"Class ID: {class_id}, Confidence: {confidence}")

                if confidence > 0.4 and class_id in relevant_class_ids:
                    found_person = True
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    obj_width = int(detection[2] * width)
                    obj_height = int(detection[3] * height)

                    x = center_x - obj_width // 2
                    y = center_y - obj_height // 2

                    cv2.rectangle(color_image, (x, y), (x + obj_width, y + obj_height), (0, 255, 0), 2)

                    distance = depth_frame.get_distance(center_x, center_y)

                    direction = get_direction(center_x, width)

                    if distance > 0:
                        label = f"Person: {distance:.2f}m, {direction}"
                        print(f"Person detected at ({center_x}, {center_y}), Distance: {distance:.2f} meters, Direction: {direction}")
                    else:
                        label = f"Person: Distance not available, {direction}"

                    cv2.putText(color_image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if not found_person:
            print("No person detected.")

        cv2.imshow("Detected People", color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()