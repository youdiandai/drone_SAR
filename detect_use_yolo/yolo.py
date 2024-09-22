import cv2
from ultralytics import YOLO
from flask import Flask, Response, render_template
import atexit
import time

rtmp_url = "rtmp://124.223.78.234:1935/live/livestream"

model = YOLO("runs/detect/train/weights/best.pt")
app = Flask(__name__)

def generate_frames():
    cap = cv2.VideoCapture(rtmp_url)
    if not cap.isOpened():
        print("Unable to open video stream.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to read frame, retrying...")
            time.sleep(1)  # 等待后重试
            continue

        results = model.track(frame, persist=True)
        annotated_frame = results[0].plot()

        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()  # 确保释放资源

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
