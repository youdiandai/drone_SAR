# drone_SAR
## start SRS service and mqtt service
start SRS service use `docker-compose -f SRS-docker-compose.yaml  up -d`.You need to ensure that you and the **SRS-docker-compose.yaml** file are in the same directory.
## start web service
```
cd detect_use_yolo
python yolo.py
```
You can visit you web in **http://127.0.0.1/5000** 

## 开启无人机推流（5分钟）
`python flight_hub.py` in directory `/detect_use_yolo`.

## 开启拉流,检测并开启web服务
`python yolo.py` in directory `/detect_use_yolo`.
