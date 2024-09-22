import cv2
from ultralytics import YOLO
from flask import Flask, Response, render_template
import atexit
import time

rtmp_url = "rtmp://124.223.78.234:1935/live/livestream"

model = YOLO("yolov8n.pt")
model = YOLO("runs/detect/train/weights/best.pt")

app = Flask(__name__)

cap = cv2.VideoCapture(rtmp_url)

def cleanup():
    if cap.isOpened():
        cap.release()

atexit.register(cleanup)

def generate_frames():
    while True:
        try:
            if not cap.isOpened():
                cap.open(rtmp_url)

            success, frame = cap.read()
            if not success:
                print("Failed to read frame, retrying...")
                continue

            results = model.track(frame, persist=True)
            annotated_frame = results[0].plot()

            _, buffer = cv2.imencode('.jpg', annotated_frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
