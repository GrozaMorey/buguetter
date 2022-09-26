import json
import requests
from mimesis import Person
from mimesis.locales import Locale


def db_script():
    count = 100
    while count > 0:
        person = Person(locale=Locale.RU)
        login = person.full_name()
        name = person.full_name()

        link = "http://127.0.0.1:5000/api/register"
        headers = {
            "content-type": "application/json"
        }
        data = {
            "login": f"{login}",
            "name": f"{name}",
            "password": "12345"
        }
        json_data = json.dumps(data)
        requests.post(link, headers=headers, data=json_data)
        f = open("user.txt", "a")
        f.write(str(data))
        f.close()
        count -= 1



