import time
import calendar
import psycopg2.extras
from app import db

DB_HOST = "localhost"
DB_NAME = "User"
DB_USER = "postgres"
DB_PASS = "123"
DB_PORT = "5432"
DB_TABLE = "users"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

def cursor_select(column, arg):
    cursor.execute(f"SELECT * FROM {DB_TABLE} WHERE {column} = '{arg}'")
    account = cursor.fetchone()
    return account


def add_user(login, name, _hashed_password):
    try:
        user = User(login, name, _hashed_password)
        db.session.add(user)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        return False


def add_token_blacklist(jti, token_exp):
    try:
        jwt = Jwt(jti, token_exp)
        db.session.add(jwt)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        return False


def get_users():
    cursor.execute(f"SELECT * FROM {DB_TABLE}")
    users = cursor.fetchall()
    return [{"id": i[0], "login": i[1], "name": i[2], "password": i[3]} for i in users]


def get_blocklist_db():
    cursor.execute(f"SELECT * FROM invalid_tokens")
    tokens = cursor.fetchall()
    result = [{"id": i[0], "jti": i[1], "date": i[2]} for i in tokens]
    current_gmt = time.gmtime()
    time_stump = calendar.timegm(current_gmt)
    for x in result:
        if int(x["date"]) <= time_stump:
            cursor.execute(f'DELETE FROM invalid_tokens WHERE id = {x["id"]}')
    return result