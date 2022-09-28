import psycopg2
import time
import calendar

DB_HOST = "containers-us-west-53.railway.app"
DB_NAME = "railway"
DB_USER = "postgres"
DB_PASS = "WJk75v28XTSv2cczzwAN"
DB_PORT = "7193"
DB_TABLE = "users2"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

def cursor_select(column, arg):
    cursor.execute(f"SELECT * FROM {DB_TABLE} WHERE {column} = '{arg}'")
    account = cursor.fetchone()
    return account


def add_user(login, name, _hashed_password):
    cursor.execute(f"INSERT INTO {DB_TABLE} (login, name, password) VALUES ('{login}','{name}','{_hashed_password}')")
    conn.commit()


def add_token_blacklist(jti, token_exp):
    cursor.execute(f"INSERT INTO invalide_tokens (jti, date) VALUES ('{jti}', '{token_exp}')")
    print(token_exp)
    conn.commit()


def get_users():
    cursor.execute(f"SELECT * FROM {DB_TABLE}")
    users = cursor.fetchall()
    return [{"id": i[0], "login": i[1], "name": i[2], "password": i[3]} for i in users]


def get_blocklist_db():
    cursor.execute(f"SELECT * FROM invalide_tokens")
    tokens = cursor.fetchall()
    result = [{"id": i[0], "jti": i[1], "date": i[2]} for i in tokens]
    current_gmt = time.gmtime()
    time_stump = calendar.timegm(current_gmt)
    for x in result:
        if int(x["date"]) <= time_stump:
            cursor.execute(f'DELETE FROM invalide_tokens WHERE id = {x["id"]}')
    return result