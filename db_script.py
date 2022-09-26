import json

import requests

def db_script():
    link = "http://127.0.0.1:5000/api/register"
    headers = {
        "content-type": "application/json"
    }
    data = {
        "login": "Vocir",
        "name": "sdfsddd",
        "password": "vcbvcfdg"
    }
    json_data = json.dumps(data)
    requests.post(link, headers=headers, data=json_data)
    f = open("user.txt", "w")
    f.write(str(data))



