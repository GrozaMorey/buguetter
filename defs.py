import time
import calendar
import psycopg2.extras
from app import db, User, Jwt, Post, Tags, db_config, logger
from flask_jwt_extended import get_jwt_identity

DB_HOST = db_config["DB_HOST"]
DB_NAME = db_config["DB_NAME"]
DB_USER = db_config["DB_USER"]
DB_PASS = db_config["DB_PASS"]
DB_PORT = db_config["DB_PORT"]
DB_TABLE = db_config["DB_TABLE"]

try:
    logger.info("psycopg2 connect run")
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    logger.info("psycopg2 connect success")
except Exception as e:
    logger.error(f"psycopg2 connect error/ {e}")


@logger.catch()
def cursor_select(column, arg):
    logger.info("cursor_select run")
    try:
        cursor.execute(f"SELECT * FROM {DB_TABLE} WHERE {column} = '{arg}'")
        account = cursor.fetchone()
        logger.info("cursor_select success")
        return account
    except Exception as e:
        logger.error(f"cursor select error/ args = {column, arg} {e}")


@logger.catch()
def add_user(login, name, _hashed_password):
    logger.info("add_user run")
    try:
        user = User(login, name, _hashed_password)
        db.session.add(user)
        db.session.commit()
        logger.info("add_user success")
        return True
    except Exception as e:
        logger.error(f"add_user error/ {e}")
        return False


@logger.catch()
def add_token_blacklist(jti, token_exp, user_id):
    logger.info("add_token_blacklist run")
    try:
        jwt = Jwt(jti, token_exp, user_id)
        db.session.add(jwt)
        db.session.commit()
        logger.info("add_token_blacklist success")
        return True
    except Exception as e:
        logger.error(f"add_token_blacklist error/ args = {jti, token_exp, user_id}  {e}")
        return False


@logger.catch()
def get_blocklist_db():
    logger.info("get_blocklist_db run")
    try:
        cursor.execute("SELECT * FROM invalid_tokens")
        tokens = cursor.fetchall()
        result = [{"id": i[0], "jti": i[1], "date": i[2], "user_id": i[3]} for i in tokens]
        time_stump = time_now()
        for x in result:
            if int(x["date"]) <= time_stump:
                cursor.execute(f'DELETE FROM invalid_tokens WHERE id = {x["id"]}')
                conn.commit()
        logger.info("get_blocklist_db success")
        return result
    except Exception as e:
        logger.error(f"get_blocklist_db error/ {e}")


@logger.catch()
def add_post(text, user_id, tags_name):
    logger.info("add_post run")
    try:
        date = time_now()
        post = Post(text, date, user_id)
        db.session.add(post)
        db.session.commit()
        tags_id_list = []
        if tags_name is not "":
            cursor.execute(f"SELECT MAX(id) FROM post WHERE user_id = {user_id}")
            post_id = cursor.fetchone()
            print(tags_name)
            for i in tags_name:
                cursor.execute(f"SELECT id FROM tags WHERE text = '{i}'")
                tags_id = cursor.fetchone()
                if not tags_id:
                    add_tag(i)
                    cursor.execute(f"SELECT id FROM tags WHERE text = ('{tags_name}')")
                    tags_id = cursor.fetchone()
                    tags_id_list.append(tags_id[0])
                else:
                    tags_id_list.append(tags_id[0])
            print(tags_id_list)
            for i in tags_id_list:
                print(i)
                post = Post.query.filter_by(id=post_id[0]).first()
                tag = Tags.query.filter_by(id=i).first()
                post.tags.append(tag)
                db.session.commit()
        logger.info("add_post success")
        return True
    except Exception as e:
        logger.error(f"add_post error/ user:{get_jwt_identity} args = {text, user_id, tags_name} {e}")
        return False


@logger.catch()
def add_tag(text):
    logger.info("add_tag run")
    try:
        tag = Tags(text)
        db.session.add(tag)
        db.session.commit()
        logger.info("add_tag success")
        return True
    except Exception as e:
        logger.error(f"add_tag error/ user:{get_jwt_identity} {e}")
        return False


@logger.catch()
def check_db():
    logger.info("check_db run")
    try:
        cursor.execute("SELECT version()")
        result = cursor.fetchone()
        if result:
            logger.info("check_db true")
            return True
        logger.info("check_db false")
        return False
    except Exception as e:
        logger.error(f"check_db error/ {e}")


@logger.catch()
def add_reaction(post_id, reaction, user_id):
    logger.info("add_reaction run")
    try:
        cursor.execute(f"UPDATE post SET {reaction} = {reaction} + 1 WHERE id = {post_id}")
        conn.commit()
        cursor.execute(f"UPDATE post SET popularity = cool + shit + angry + nice WHERE id = {post_id}")
        cursor.execute(f"UPDATE post SET karma = cool + nice - shit - angry WHERE id = {post_id}")
        cursor.execute(f"UPDATE post SET total = popularity + karma WHERE id = {post_id}")
        conn.commit()

        cursor.execute(f"SELECT tag_id FROM post_tags WHERE post_id = {post_id}")
        tags = cursor.fetchall()
        if tags is not None:
            sign = "-"
            if reaction in ["cool", "nice"]:
                sign = "+"
                post = Post.query.filter_by(id=post_id).first()
                user = User.query.filter_by(id=user_id).first()
                user.user_post_likes.append(post)
                db.session.commit()
            cursor.execute(f"SELECT tag_id FROM user_tags WHERE user_id = {user_id}")
            karma = cursor.fetchall()
            user = User.query.filter_by(id=user_id).first()
            for i in tags:
                if i in karma:
                    logger.info("add_reaction put + karma for user_tags")
                    cursor.execute(f"UPDATE user_tags SET karma_tag = karma_tag {sign} 1 WHERE user_id = {user_id}"
                                   f" and tag_id = {i[0]}")
                    conn.commit()
                else:
                    logger.info("add_reaction put - karma for user_tags")
                    tag = Tags.query.filter_by(id=i[0]).first()
                    user.user_tags.append(tag)
                    db.session.commit()
                    cursor.execute(f"UPDATE user_tags SET karma_tag = karma_tag {sign} 1 WHERE user_id = {user_id}"
                                   f" and tag_id = {i[0]}")
                    conn.commit()
            logger.info("add_reaction success")
            return True
    except Exception as e:
        logger.error(f"add_reaction error/ user:{user_id} {e}")
        return False


@logger.catch()
def get_seen_post(user_id):
    logger.info("get_seen_post run")
    try:
        # Список постов который видел юзер
        cursor.execute(f"SELECT * FROM user_post WHERE user_id = {user_id}")
        result = cursor.fetchall()
        post_id = []
        date = time_now()
        for i in result:
            post_id.append(i[1])
            if i[2] <= date:
                cursor.execute(f"DELETE FROM user_post WHERE user_id = {i[0]} and post_id = {i[1]}")
                logger.info("get_seen_post run")
        return post_id
    except Exception as e:
        logger.error(f"get_seen_post error/ user:{get_jwt_identity} args = {user_id} {e}")


@logger.catch()
def get_feed(post_id, user_id):
    logger.info("get_feed run")
    try:
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

        # вывод постов по тоталу и формирование словаря содержащий карму тега
        date = time_now()
        cursor.execute(f"SELECT * FROM post WHERE date BETWEEN {date - 604800} and {date} ORDER BY total DESC")
        result = cursor.fetchall()
        cursor.execute(f"SELECT tag_id, karma_tag FROM user_tags WHERE user_id = {user_id} ORDER BY karma_tag DESC")
        favorite_tags = cursor.fetchall()
        tag_karma = {}
        for i in favorite_tags:
            tag_karma[f"{i[0]}"] = i[1]
        data = []
        num = 1
        post_seen = get_seen_post(user_id)
        for i in result:
            # чек id поста на наличие в увиденном
            if i[0] in post_seen:
                continue
            else:
                data.append({
                    "id": i[0],
                    "text": i[1],
                    "date": i[2],
                    "user_id": i[3],
                    "total": i[9]})
                # суммирование тотала поста с кармой тега
                cursor.execute(f"SELECT tag_id from post_tags WHERE post_id ={i[0]}")
                tags = extract_sql_array(cursor.fetchall())
                for j in extract_sql_array(favorite_tags):
                    if j in tags:
                        index_post = data[-1]
                        index_post["total"] += tag_karma[f"{j}"] * 2

                num += 1
        post_list = sorted(data, key=lambda k: k['total'], reverse=True)
        num = 1
        data = {}
        for i in post_list:
            data[f"{num}"] = i
            num += 1
        logger.info("get_feed success")
        return data
    except Exception as e:
        logger.error(f"get_feed error/ user:{user_id} args = {post_id} {e}")


def get_user_data(user_id):
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    result = cursor.fetchone()
    return {"user_id": result[0], "name": result[2]}


@logger.catch()
def extract_sql_array(array):
    try:
        # достает данные из листа sql
        result = []
        for i in array:
            result.append(i[0])
        return result
    except Exception as e:
        logger.error(f"extract_sql_array error/ user:{get_jwt_identity} {e}")


@logger.catch()
def time_now():
    logger.info("time_now run")
    try:
        # штамп данного времени
        current_gmt = time.gmtime()
        result = calendar.timegm(current_gmt)
        logger.info("time_now success")
        return result
    except Exception as e:
        logger.error(f"time_now error/ {e}")


@logger.catch()
def get_post_user(user_id):
    logger.info("get_post_user run")
    try:
        data = {}
        cursor.execute(f"SELECT * FROM post WHERE user_id = {user_id}")
        result = cursor.fetchall()
        if not result:
            return {"msg": "error", "error": 15}
        for i in result:
            data[f"{i[0]}"] = {
                "text": i[1],
                "data": i[2],
                "reactions": {
                "cool": i[4],
                "shit": i[5],
                "angry": i[6],
                "nice": i[10]}
            }
        return data
    except Exception as e:
        logger.error(f"get_post_user error/ user:{user_id} {e}")


def get_likes(user_id):
    logger.info("get_likes run")
    try:
        cursor.execute(f"SELECT post_id FROM user_post_likes WHERE user_id = {user_id}")
        post_id = []
        data = {}
        result = cursor.fetchall()
        if not result:
            return {"msg": "error", "error": 14}
        for i in result:
            post_id.append(i[0])
        cursor.execute(f"SELECT * FROM post WHERE id in ({str(post_id)[1:-1]})")
        result = cursor.fetchall()
        for i in result:
            data[f"{i[0]}"] = {
                "text": i[1],
                "data": i[2],
                "reactions": {
                "cool": i[4],
                "shit": i[5],
                "angry": i[6],
                "nice": i[10]}
            }
        logger.info("get_likes success")
        return data
    except Exception as e:
        logger.error(f"get_likes error/ user:{user_id} {e}")


def get_another_user_data(name):
    logger.info("get_another_user_data run")
    try:
        cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
        result = cursor.fetchone()
        return {"user_id": result[0]}
    except Exception as e:
        logger.error(f"get_another_user_data error/args = {name} {e}")
        return {"msg": "error", "error": 15}