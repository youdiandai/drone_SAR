import requests
import json

organization_key = "a8e241f4446ba3291b070b497337e33713b5abb97cc583ac92d5de24406764bc"
dji_url = "https://es-flight-api-cn.djigate.com"

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
    print(response.text)
    return response.text

def get_device_by_project_id(project_id):
    """获取项目下的设备列表

    Args:
        project_id (_type_): _description_

    Returns:
        _type_: _description_
    """
    import requests
    url = dji_url+f"/manage/api/v1.0/projects/{project_id}/devices"
    payload={}
    headers = {
        'X-Organization-Key': f'{organization_key}',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.text

if __name__ == '__main__':
    print(get_project_list())
    print("*"*100)
    print(get_device_by_project_id("aad2f7cd-db27-4226-b2d7-8b4b36422df5"))