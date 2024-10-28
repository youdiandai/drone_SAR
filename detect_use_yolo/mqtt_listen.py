import paho.mqtt.client as mqtt
import json
import sys
import math

#mqtt_server = "localhost"
mqtt_server = "124.223.78.234"


def on_message_to_flask(client, userdata, message):
    try:
        payload_json = message.payload.decode('utf-8')
        payload_data = json.loads(payload_json)
        print(payload_data)
        # 更新全局变量中的最新MQTT消息
        global latest_mqtt_message
        latest_mqtt_message = payload_data
    except Exception as e:
        print(f"Error decoding JSON: {e}")


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
    client.connect(mqtt_server, 1883, 60)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()



def wgs84_to_gcj02(lon, lat):
    """
    将WGS84坐标转换为GCJ-02坐标
    :param lon: WGS84的经度
    :param lat: WGS84的纬度
    :return: (gcj_lon, gcj_lat)转换后的GCJ-02坐标
    """
    # 定义一些常数
    a = 6378245.0  # 长半轴
    ee = 0.006693421622965943  # 偏心率平方

    # 判断是否在中国范围内
    def out_of_china(lon, lat):
        return not (73.66 < lon < 135.05) or not (3.86 < lat < 53.55)

    # 转换函数
    def transform(lon, lat):
        dlat = _transform_lat(lon - 105.0, lat - 35.0)
        dlon = _transform_lon(lon - 105.0, lat - 35.0)
        radLat = lat / 180.0 * math.pi
        magic = math.sin(radLat)
        magic = 1 - ee * magic * magic
        sqrtMagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * math.pi)
        dlon = (dlon * 180.0) / (a / sqrtMagic * math.cos(radLat) * math.pi)
        mgLat = lat + dlat
        mgLon = lon + dlon
        return mgLon, mgLat

    def _transform_lat(x, y):
        lat = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
        lat += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
        lat += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
        lat += (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
        return lat

    def _transform_lon(x, y):
        lon = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        lon += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
        lon += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
        lon += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
        return lon

    if out_of_china(lon, lat):
        return lon, lat
    else:
        return transform(lon, lat)



if __name__ == "__main__":
    # 从命令行获取 device_sn 参数
    if len(sys.argv) > 1:
        device_sn = sys.argv[1]
    else:
        device_sn = "7CTDM3800B883B"  # 如果没有提供参数，使用默认值
#M3TD 1581F6Q8D243N00CPVGL
#DOCK2 7CTDM3800B883B
    # 调用函数并传递设备序列号
    subscribe_to_topic(device_sn)
