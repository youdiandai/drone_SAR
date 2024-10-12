import paho.mqtt.client as mqtt
# Topic:thing/product/{device_sn}/osd
# MQTT服务器地址和端口
device_sn = "7CTDM3800B883B"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = f"thing/product/{device_sn}/osd"

# MQTT用户名和密码
MQTT_USERNAME = "admin"
MQTT_PASSWORD = "admin123"

# MQTT消息回调函数
def on_message(client, userdata, message):
    print(f"Received message '{str(message.payload)}' on topic '{message.topic}' with QoS {message.qos}")

# 创建MQTT客户端实例
client = mqtt.Client(protocol=mqtt.MQTTv5)  # 使用 MQTT v5 协议

# 设置用户名和密码
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# 指定消息回调函数
client.on_message = on_message

# 连接到MQTT服务器
client.connect(MQTT_BROKER, MQTT_PORT)

# 订阅主题
client.subscribe(MQTT_TOPIC)

# 阻塞调用，直到客户端断开连接
client.loop_forever()
