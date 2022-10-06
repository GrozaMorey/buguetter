import json
import time
import calendar
import psycopg2.extras
from app import db, User, Jwt, Post, Tags, db_config
from datetime import datetime
from flask import Response


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
    cursor.execute("SELECT * FROM invalid_tokens")
    tokens = cursor.fetchall()
    result = [{"id": i[0], "jti": i[1], "date": i[2], "user_id": i[3]} for i in tokens]
    current_gmt = time.gmtime()
    time_stump = calendar.timegm(current_gmt)
    for x in result:
        if int(x["date"]) <= time_stump:
            cursor.execute(f'DELETE FROM invalid_tokens WHERE id = {x["id"]}')
            conn.commit()
    return result


def add_post(text, user_id, tags_id):
    try:
        date = time_now()
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


def add_reaction(post_id, reaction, user_id):
    try:
        cursor.execute(f"UPDATE post SET {reaction} = {reaction} + 1 WHERE id = {post_id}")
        conn.commit()
        cursor.execute(f"UPDATE post SET popularity = cool + shit + angry WHERE id = {post_id}")
        cursor.execute(f"UPDATE post SET karma = cool - shit - angry WHERE id = {post_id}")
        cursor.execute(f"UPDATE post SET total = popularity + karma WHERE id = {post_id}")
        conn.commit()

        cursor.execute(f"SELECT tag_id FROM post_tags WHERE post_id = {post_id}")
        tags = cursor.fetchall()
        if tags is not None:
            sign = "-"
            if reaction in ["cool"]:
                sign = "+"
            cursor.execute(f"SELECT tag_id FROM user_tags WHERE user_id = {user_id}")
            karma = cursor.fetchall()
            user = User.query.filter_by(id=user_id).first()
            for i in tags:
                if i in karma:
                    cursor.execute(f"UPDATE user_tags SET karma_tag = karma_tag {sign} 1 WHERE user_id = {user_id} and tag_id = {i[0]}")
                    conn.commit()
                else:
                    tag = Tags.query.filter_by(id=i[0]).first()
                    user.user_tags.append(tag)
                    db.session.commit()
                    cursor.execute(f"UPDATE user_tags SET karma_tag = karma_tag {sign} 1 WHERE user_id = {user_id} and tag_id = {i[0]}")
                    conn.commit()
            return True
    except Exception as e:
        print(e)
        return False


def get_seen_post(user_id):
    cursor.execute(f"SELECT * FROM user_post WHERE user_id = {user_id}")
    result = cursor.fetchall()
    post_id = []
    date = time_now()
    for i in result:
        post_id.append(i[1])
        if i[2] <= date:
            cursor.execute(f"DELETE FROM user_post WHERE user_id = {i[0]} and post_id = {i[1]}")
    return post_id


def get_feed(post_id, user_id):
    # добавление поста в игнор лист

    if post_id is not False:
        user = User.query.filter_by(id=user_id).first()
        for i in post_id:
            post = Post.query.filter_by(id=i).first()
            user.post_seen.append(post)
            db.session.commit()
            cursor.execute(f"SELECT date FROM post WHERE id = {i}")
            result = cursor.fetchone()
            cursor.execute(f"UPDATE user_post SET date = {result[0]} + 604800 WHERE post_id = {i}")
            conn.commit()

    # вывод постов

    date = time_now()
    cursor.execute(f"SELECT * FROM post WHERE date BETWEEN {date - 604800} and {date} ORDER BY total DESC")
    result = cursor.fetchall()
    cursor.execute(f"SELECT tag_id, karma_tag FROM user_tags WHERE user_id = {user_id} ORDER BY karma_tag DESC")
    favorite_tags = cursor.fetchall()
    karma_tag = {}
    for i in favorite_tags:
        karma_tag[f"{i[0]}"] = i[1]
    data = []
    num = 1
    post_seen = get_seen_post(user_id)
    for i in result:
        if i[0] in post_seen:
            continue
        else:
            data.append( {
                "id": i[0],
                 "text": i[1],
                 "date": i[2],
                 "user_id": i[3],
                 "total": i[9]})
            cursor.execute(f"SELECT tag_id from post_tags WHERE post_id ={i[0]}")
            tags = extract_sql_array(cursor.fetchall())
            num_of_favorite_tags = 0
            for j in extract_sql_array(favorite_tags):
                if j in tags:
                    g = favorite_tags[num_of_favorite_tags]
                    index_post = data[-1]
                    index_post["total"] += karma_tag[f"{j}"] * 2
                    num_of_favorite_tags += 1

            num += 1
    post_list = sorted(data, key=lambda k: k['total'], reverse=True)
    num = 1
    data = {}
    for i in post_list:
        data[f"{num}"] = i
        num += 1
    return data


def get_user_date(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    result = cursor.fetchone()
    return result[2]

# достает данные из листа sql

def extract_sql_array(array):
    result = []
    for i in array:
        result.append(i[0])

    return result

# штамп данного времени

def time_now():
    current_gmt = time.gmtime()
    result = calendar.timegm(current_gmt)
    return result
