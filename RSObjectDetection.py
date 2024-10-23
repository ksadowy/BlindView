import pyrealsense2 as rs
import numpy as np
import cv2

net = cv2.dnn.readNet("yolov3-tiny.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

classes = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", 
           "truck", "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", 
           "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", 
           "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", 
           "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", 
           "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", 
           "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", 
           "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", 
           "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed", 
           "dining table", "toilet", "TV", "laptop", "mouse", "remote", "keyboard", 
           "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", 
           "book", "clock", "vase", "scissors", "teddy bear", "hair dryer", 
           "toothbrush"]

relevant_class_ids = [0, 14, 56, 59]

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

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

        blob = cv2.dnn.blobFromImage(color_image, 1 / 255.0, (320, 320), (0, 0, 0), swapRB=True, crop=False)
        net.setInput(blob)

        detections = net.forward(output_layers)

        height, width, _ = color_image.shape

        for output in detections:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if confidence > 0.5 and class_id in relevant_class_ids:
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    obj_width = int(detection[2] * width)
                    obj_height = int(detection[3] * height)

                    x = center_x - obj_width // 2
                    y = center_y - obj_height // 2

                    cv2.rectangle(color_image, (x, y), (x + obj_width, y + obj_height), (0, 255, 0), 2)

                    object_label = classes[class_id]
                    direction = get_direction(center_x, width)

                    distance = depth_frame.get_distance(center_x, center_y)

                    if distance > 0:
                        label = f"{object_label}: {distance:.2f}m, {direction}"
                        print(f"{object_label} detected at ({center_x}, {center_y}), Distance: {distance:.2f} meters, Direction: {direction}")
                    else:
                        label = f"{object_label}: Distance not available, {direction}"

                    cv2.putText(color_image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Detected Objects", color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()