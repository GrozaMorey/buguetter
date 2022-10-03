import time
import calendar
import psycopg2.extras
from app import db, User, Jwt, Post, Tags, db_config
from datetime import datetime


DB_HOST = db_config["DB_HOST"]
DB_NAME = db_config["DB_NAME"]
DB_USER = db_config["DB_USER"]
DB_PASS = db_config["DB_PASS"]
DB_PORT = db_config["DB_PORT"]
DB_TABLE = db_config["DB_TABLE"]

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


def add_token_blacklist(jti, token_exp, user_id):
    try:
        jwt = Jwt(jti, token_exp, user_id)
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
    result = [{"id": i[0], "jti": i[1], "date": i[2], "user_id": i[3]} for i in tokens]
    current_gmt = time.gmtime()
    time_stump = calendar.timegm(current_gmt)
    for x in result:
        if int(x["date"]) <= time_stump:
            cursor.execute(f'DELETE FROM invalid_tokens WHERE id = {x["id"]}')
    return result


def add_post(text, user_id, tags_id):
    try:
        current_gmt = time.gmtime()
        date = calendar.timegm(current_gmt)
        post = Post(text, date, user_id)
        db.session.add(post)
        db.session.commit()
        if tags_id != 0:
            cursor.execute(f"SELECT MAX(id) FROM post WHERE user_id = {user_id}")
            id = cursor.fetchone()
            for i in tags_id:
                post = Post.query.filter_by(id=id[0]).first()
                tag = Tags.query.filter_by(id=i).first()
                post.tags.append(tag)
                db.session.commit()


        return True
    except Exception as e:
        print(e)
        return False

def add_tag(text):
    try:
        tag = Tags(text)
        db.session.add(tag)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        return False

def check_db():
    try:
        cursor.execute("SELECT version()")
        result = cursor.fetchone()
        if result:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

def add_reaction(post_id, reaction):
    try:
        cursor.execute(f"UPDATE post SET {reaction} = {reaction} + 1 WHERE id = {post_id}")
        conn.commit()
        cursor.execute(f"UPDATE post SET popularity = cool + shit + angry WHERE id = {post_id}")
        cursor.execute(f"UPDATE post SET karma = cool - shit - angry WHERE id = {post_id}")
        cursor.execute(f"UPDATE post SET total = popularity + karma WHERE id = {post_id}")
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False

def get_feed(offset):
    current_gmt = time.gmtime()
    date = calendar.timegm(current_gmt)
    if offset == None:
        cursor.execute(f"SELECT * FROM post WHERE date BETWEEN {date - 604800} and {date} ORDER BY total DESC LIMIT 10")
        result = cursor.fetchall()
        data = {}
        num = 1
        for i in result:
            data[f"{num}"] =(
                {"id": i[0],
                "text": i[1],
                "date": i[2],
                "user_id": i[3]})
            num += 1
        return data
    else:
        cursor.execute(f"SELECT * FROM post WHERE date BETWEEN {date - 604800} and {date} ORDER BY total DESC LIMIT 10 OFFSET {offset}")
        result = cursor.fetchall()
        data = {}
        num = 1
        for i in result:
            data[f"{num}"] = (
                {"id": i[0],
                 "text": i[1],
                 "date": i[2],
                 "user_id": i[3]})
            num += 1
        return data

def get_user_date(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    result = cursor.fetchone()
    return result[2]
