import paho.mqtt.client as mqtt

# MQTT服务器地址和端口
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "test/topic"
MQTT_MESSAGE = "Hello from Python!"

# MQTT用户名和密码
MQTT_USERNAME = "admin"
MQTT_PASSWORD = "admin123"

# 创建MQTT客户端实例
client = mqtt.Client()

# 设置用户名和密码
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

# 连接到MQTT服务器
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# 发布消息
client.publish(MQTT_TOPIC, MQTT_MESSAGE)

# 断开连接
client.disconnect()
