import cv2
from ultralytics import YOLO
from ultralytics.engine.results import Results
from flask import Flask, Response, render_template, jsonify
import time
import threading
from collections import deque
import mqtt_listen  # 直接导入模块
from datetime import datetime, timezone, timedelta
from flight_hub import start_rtmp_stream,stop_rtmp_stream,stop_all_live_streams_of_mt3
import sys
import signal
import json





rtmp_url = "rtmp://124.223.78.234:1935/live/livestream"

model = YOLO("runs/detect/train/weights/best.pt")

app = Flask(__name__)

video_stream_start_timestamp = time.time()
start_msg = {"message":"No"}

frame_queue = deque(maxlen=200)
frame_lock = threading.Lock()
fps = 0
frame_count = 0
start_time = time.time()

# 记录程序启动时间
program_start_time = time.time()

def cleanup():
    """清理工作"""
    global start_msg
    print("Stopping RTMP stream...")
    stop_all_live_streams_of_mt3()
    print("Cleanup complete, exiting program.")

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

def convert_to_beijing_time(timestamp):
    """
    将时间戳转换为北京时间（UTC+8），支持秒级和毫秒级输入。
    秒级时间戳会补上 .000 毫秒，毫秒级时间戳则保留其毫秒部分。

    Args:
        timestamp (int): 时间戳，单位可以是秒或毫秒。

    Returns:
        str: 格式化的北京时间字符串（带毫秒）。
    """
    if len(str(timestamp)) == 13:  # 毫秒级时间戳
        timestamp_s = timestamp / 1000
        ms_part = datetime.fromtimestamp(timestamp_s, timezone.utc).strftime('%f')[:3]
    elif len(str(timestamp)) == 10:  # 秒级时间戳
        timestamp_s = timestamp
        ms_part = "000"
    else:
        raise ValueError("时间戳格式不正确，请输入10位或13位的整数。")

    # 转换为 UTC 时间并加上8小时
    utc_time = datetime.fromtimestamp(timestamp_s, timezone.utc)
    beijing_time = utc_time + timedelta(hours=8)

    # 格式化输出并包含毫秒
    return f"{beijing_time.strftime('%Y-%m-%d %H:%M:%S')}.{ms_part}"

def calculate_video_frame_timestamp(video_start_timestamp, frame_timestamp):
    """
    将视频流帧的时间戳和开始时间戳相加，并返回完整的北京时间。
    
    Args:
        video_start_timestamp (int): 视频开始时间戳（Unix 时间戳，单位为秒）。
        frame_timestamp (float): 帧时间戳（相对于视频开始的时间戳，单位为秒）。

    Returns:
        str: 格式化的北京时间字符串，精确到毫秒。
    """
    # 将开始时间戳和帧时间戳相加得到当前时间戳
    total_timestamp = video_start_timestamp + frame_timestamp
    
    # 转换为 UTC 时间并加上8小时（北京时间）
    utc_time = datetime.fromtimestamp(total_timestamp, timezone.utc)
    beijing_time = utc_time + timedelta(hours=8)

    # 格式化输出，保留毫秒
    return beijing_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

def filter_class(r:Results):
    """过滤其他类别只留下person

    Args:
        r (Results): yolo的检测结果

    Returns:
        _type_: 过滤后的检测结果
    """
    r.boxes=[x for x in  r.boxes if r.names[int(x.cls)]=="person"]
    return r

def frame_reader():
    global video_stream_start_timestamp
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

        # 获取时间戳，单位为毫秒，将其转换为秒
        tmp_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
        # print(f"timestamp from video stream:{str(tmp_timestamp)},video_stream_strap_timestamp:{str(video_stream_start_timestamp)} ,added timestamp:{str(tmp_timestamp+video_stream_start_timestamp)}")
        timestamp_ms = tmp_timestamp+video_stream_start_timestamp*1000
        # timestamp = timestamp_ms / 1000

        with frame_lock:
            if len(frame_queue) >= frame_queue.maxlen:
                frame_queue.popleft()
            # 将帧和时间戳作为元组存储
            frame_queue.append((frame, timestamp_ms))

    cap.release()


def generate_frames():
    global fps, frame_count
    while True:
        with frame_lock:
            if not frame_queue:
                continue
            frame, timestamp = frame_queue.popleft()

        frame_process_start_time = time.time()

        results = model.track(frame, persist=True)
        filter_class(results[0])
        annotated_frame = results[0].plot()

        frame_process_end_time = time.time()

        frame_count += 1
        elapsed_time = frame_process_end_time - frame_process_start_time

        if elapsed_time > 0:
            current_fps = 1 / elapsed_time
            fps = (fps * (frame_count - 1) + current_fps) / frame_count

        # 添加 FPS 和时间戳
        cv2.putText(annotated_frame, f'FPS: {int(fps)}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated_frame, f'Timestamp: {convert_to_beijing_time(int(timestamp))}', 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

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
            'longitude': mqtt_listen.latest_mqtt_message["longitude"],
            'timestamp': convert_to_beijing_time(mqtt_listen.latest_mqtt_message["timestamp"])
        })


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)  # 捕获 Ctrl+C 信号
    device_sn = "1581F6Q8D243N00CPVGL"
    
    # 仅在未成功推流时执行
    if start_msg['message'] != "OK":
        start_message = start_rtmp_stream(device_sn, "81-0-0", "cxtest")
        start_msg = json.loads(start_message)
        print(f"start message :{start_msg}")
    
    try:
        video_stream_start_timestamp = start_msg['data']['create_ts']
        print(f"video stream start timestamp :{video_stream_start_timestamp},beijing time :{convert_to_beijing_time(video_stream_start_timestamp)}")
        
        mqtt_listener_thread = threading.Thread(target=mqtt_listen.subscribe_to_topic, args=(device_sn,))
        mqtt_listener_thread.start()

        reader_thread = threading.Thread(target=frame_reader)
        reader_thread.start()
        
        # 关闭自动重载
        app.run(debug=True, threaded=True, use_reloader=False)

        program_end_time = time.time()
        print(f"Program started in {program_end_time - program_start_time:.2f} seconds")
    except:
        cleanup()
    finally:
        cleanup()

