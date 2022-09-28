from mimesis import Person
from mimesis.locales import Locale
from defs import add_user
from werkzeug.security import generate_password_hash



def db_script():
    count = 1000
    _hashed_password = generate_password_hash("12345")
    while count > 0:
        person = Person(locale=Locale.RU)
        login = person.full_name()
        name = person.name()
        add_user(login, name, _hashed_password)
        print("done")
        count -= 1



