import requests
import os
from datetime import datetime

API_KEY = "1iJIyS4JsjvOZMKXR3nOGIFuKovjK2YOvza4XgDm8"
BASE_URL = "http://pingnas.mammoth-alioth.ts.net:2283/api"

def upload(file):
    stats = os.stat(file)
    headers = {
        'Accept':'application/json',
        'x-api-key':API_KEY
    }
    data = {
        'deviceAssetId': f'{file}-{stats.st_mtime}',
        'deviceId': 'python',
        'fileCreatedAt': datetime.fromtimestamp(stats.st_mtime),
        'fileModifiedAt': datetime.fromtimestamp(stats.st_mtime),
        'isFavorite': 'false',
    }
    files = {
        'assetData':open(file,'rb')
    }
    response = requests.post(
        f'{BASE_URL}/assets', headers=headers, data=data, files=files)

    print(response.json())
upload('./test.jpg')