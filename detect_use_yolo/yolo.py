import cv2
from ultralytics import YOLO
from flask import Flask, Response, render_template, jsonify
import time
import threading
from collections import deque
import mqtt_listen  # 直接导入模块

rtmp_url = "rtmp://124.223.78.234:1935/live/livestream"

model = YOLO("runs/detect/train/weights/best.pt")

app = Flask(__name__)

frame_queue = deque(maxlen=200)
frame_lock = threading.Lock()
fps = 0
frame_count = 0
start_time = time.time()

# 记录程序启动时间
program_start_time = time.time()

def frame_reader():
    cap = cv2.VideoCapture(rtmp_url)
    if not cap.isOpened():
        print("Unable to open video stream.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to read frame, retrying...")
            time.sleep(1)
            continue
        
        with frame_lock:
            if len(frame_queue) >= frame_queue.maxlen:
                frame_queue.popleft()
            frame_queue.append(frame)

    cap.release()

def generate_frames():
    global fps, frame_count
    while True:
        with frame_lock:
            if not frame_queue:
                continue
            frame = frame_queue.popleft()

        frame_process_start_time = time.time()

        results = model.track(frame, persist=True)
        annotated_frame = results[0].plot()

        frame_process_end_time = time.time()

        frame_count += 1
        elapsed_time = frame_process_end_time - frame_process_start_time

        if elapsed_time > 0:
            current_fps = 1 / elapsed_time
            fps = (fps * (frame_count - 1) + current_fps) / frame_count

        cv2.putText(annotated_frame, f'FPS: {int(fps)}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/latest-mqtt-message')
def latest_mqtt_message_route():
    with mqtt_listen.message_lock:  # 保护读取
        return jsonify({
            'latitude': mqtt_listen.latest_mqtt_message["latitude"],
            'longitude': mqtt_listen.latest_mqtt_message["longitude"]
        })


if __name__ == "__main__":
    device_sn = "1581F6Q8D243N00CPVGL"
    # device_sn = "1581F6Q8D243N00CPVGL"

    mqtt_listener_thread = threading.Thread(target=mqtt_listen.subscribe_to_topic, args=(device_sn,))
    mqtt_listener_thread.start()

    reader_thread = threading.Thread(target=frame_reader)
    reader_thread.start()
    app.run(debug=True, threaded=True)

    program_end_time = time.time()
    print(f"Program started in {program_end_time - program_start_time:.2f} seconds")
