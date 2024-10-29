import requests
import json
import time

organization_key = "a8e241f4446ba3291b070b497337e33713b5abb97cc583ac92d5de24406764bc"
dji_url = "https://es-flight-api-cn.djigate.com"
rtmp_server = "rtmp://124.223.78.234:1935/live/livestream"

def get_project_list():
    """获取组织下的项目列表
    Returns:
        _type_: _description_
    """
    url =dji_url+"/manage/api/v1.0/projects?page=1&page_size=10"
    payload = json.dumps({})
    headers = {
        'X-Organization-Key': f'{organization_key}',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.text

def get_device_by_project_id(project_id):
    """获取项目下的设备列表

    Args:
        project_id (_type_): 设备列表

    Returns:
        _type_: _description_
    """
    url = dji_url+f"/manage/api/v1.0/projects/{project_id}/devices"
    payload={}
    headers = {
        'X-Organization-Key': f'{organization_key}',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.text

def start_rtmp_stream(service_sn,camera_id,convert_id):
    url = dji_url+"/manage/api/v1.0/stream-converters"
    payload = json.dumps({
        "region": "cn",
        "converter_name": f"{convert_id}",
        "sn": f"{service_sn}",
        "camera": f"{camera_id}",
        "video": "normal-0",
        "idle_timeout": 60,
        "video_quality": 0,
        "bypass_option": {
            "url": f"{rtmp_server}"
        },"rtmp_url": f"{rtmp_server}"})
    headers = {
    'X-Organization-Key': f'{organization_key}',
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text

def stop_rtmp_stream(convert_id):
    url = dji_url+f"/manage/api/v1.0/stream-converters/{convert_id}"
    payload={}
    headers = {
    'X-Organization-Key': f'{organization_key}',
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
    }
    response = requests.request("DELETE", url, headers=headers, data=payload)

    return response.text

def flight_hub_livestream_5_min():
    """
    开启机巢中无人机5分钟视频流
    """
    start_message  = start_rtmp_stream("1581F6Q8D243N00CPVGL","81-0-0","cxtest")
    start_msg = json.loads(start_message)
    print(start_msg)
    time.sleep(60*5)
    if start_msg['message']=='OK':
        print(stop_rtmp_stream(start_msg['data']['data']['converter_id']))
        print(f"{start_msg['data']['data']['converter_id']} stoped")

if __name__ == '__main__':
    # print(json.loads(get_device_by_project_id("aad2f7cd-db27-4226-b2d7-8b4b36422df5")))
    flight_hub_livestream_5_min()