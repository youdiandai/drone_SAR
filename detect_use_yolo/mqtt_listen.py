import paho.mqtt.client as mqtt
import json
import sys

def on_message(client, userdata, message):
    try:
        # 将收到的消息转换为 JSON 对象
        payload_json = message.payload.decode('utf-8')
        payload_data = json.loads(payload_json)
        print(payload_data)
    except Exception as e:
        print(f"Error decoding JSON: {e}")

def subscribe_to_topic(device_sn):
    MQTT_TOPIC = f"thing/product/{device_sn}/osd"
    client = mqtt.Client(protocol=mqtt.MQTTv5)  # 使用 MQTT v5 协议
    client.username_pw_set("admin", "admin123")
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()


if __name__ == "__main__":
    # 从命令行获取 device_sn 参数
    if len(sys.argv) > 1:
        device_sn = sys.argv[1]
    else:
        device_sn = "7CTDM3800B883B"  # 如果没有提供参数，使用默认值

    # 调用函数并传递设备序列号
    subscribe_to_topic(device_sn)
