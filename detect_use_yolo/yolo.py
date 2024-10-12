import cv2
from ultralytics import YOLO
from flask import Flask, Response, render_template
import time
import threading
from collections import deque

rtmp_url = "rtmp://124.223.78.234:1935/live/livestream"

model = YOLO("runs/detect/train/weights/best.pt")
app = Flask(__name__)

frame_queue = deque(maxlen=200)  # 增加队列大小以容纳更多帧
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
        
        # 将帧时间戳添加到队列
        with frame_lock:
            if len(frame_queue) >= frame_queue.maxlen:
                frame_queue.popleft()  # 丢弃最旧的帧
            frame_queue.append(frame)  # 只添加帧，不再添加时间戳

    cap.release()

def generate_frames():
    global fps, frame_count, start_time
    while True:
        with frame_lock:
            if not frame_queue:
                continue  # 等待新帧
            frame = frame_queue.popleft()  # 取出帧

        # 记录处理开始时间
        frame_process_start_time = time.time()

        results = model.track(frame, persist=True)
        annotated_frame = results[0].plot()

        # 记录处理结束时间
        frame_process_end_time = time.time()

        # 更新帧率
        frame_count += 1
        elapsed_time = frame_process_end_time - frame_process_start_time

        # 计算FPS
        if elapsed_time > 0:
            current_fps = 1 / elapsed_time
            fps = (fps * (frame_count - 1) + current_fps) / frame_count  # 平滑计算FPS

        # 在帧上绘制帧率
        cv2.putText(annotated_frame, f'FPS: {int(fps)}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    reader_thread = threading.Thread(target=frame_reader)
    reader_thread.start()
    app.run(debug=True, threaded=True)

    # 计算并打印程序启动时间
    program_end_time = time.time()
    print(f"Program started in {program_end_time - program_start_time:.2f} seconds")