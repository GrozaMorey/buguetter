import time
import calendar
from app import *
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, create_refresh_token, get_jwt, jwt_required


def add_token_blacklist(jti, token_exp, user_id):
    logger.info("add_token_blacklist run")
    try:
        jwt = Jwt(jti, int(token_exp), user_id)
        db.session.add(jwt)
        db.session.commit()
        logger.info("add_token_blacklist success")
        return True
    except Exception as e:
        logger.error(f"add_token_blacklist error/ args = {jti, token_exp, user_id}  {e}")
        return False


def get_blocklist_db():
    logger.info("get_blocklist_db run")
    try:
        jwt = Jwt.query.all()
        time_stump = time_now()
        for x in jwt:
            if x.date <= time_stump:
                delete = Jwt.query.filter_by(id=x.id).delete()
                db.session.add(delete)
        db.session.commit()
        logger.info("get_blocklist_db success")
        return jwt
    except Exception as e:
        logger.error(f"get_blocklist_db error/ {e}")


def time_now():
    logger.info("time_now run")
    try:
        current_gmt = time.gmtime()
        result = calendar.timegm(current_gmt)
        logger.info("time_now success")
        return result
    except Exception as e:
        logger.error(f"time_now error/ {e}")


def register(login, name, password):
    logger.info("register run")
    try:
        _hashed_password = generate_password_hash(password)
        if db.session.query(User.id).filter_by(login=login).first():
            return False
        date = time_now()
        user = User(login, name, _hashed_password, date)
        db.session.add(user)
        db.session.commit()
        logger.info("register success")
        return True
    except Exception as error:
        logger.error(f"register error {error}")


def loging(login, password):
    logger.info("login run")
    try:
        if db.session.query(User.id).filter_by(login=login).first():
            for i in db.session.query(User.password).filter_by(login=login).first():
                if check_password_hash(i, password) is True:
                    account = db.session.query(User.id, User.password).filter_by(login=login).first()
                    identify = {
                        "user_id": account[0],
                        "username": account[1]
                    }
                    token = create_access_token(identity=identify)
                    refresh_token = create_refresh_token(identity=identify)
                    logger.info("login success")
                    return token, refresh_token
            return "error"
        return "error"
    except Exception as error:
        logger.error(f"login error/ {error}")
        return False


def feed(offset, limit, selection, id):
    if id == 0:
        id = get_jwt_identity()["user_id"]
    match selection:
        case "profile":
            return Post.query.filter_by(author=id).offset(offset).limit(limit).all()
        case "profile_likes":
            user = User.query.filter_by(id=id).first()
            return user.user_post_likes
        case "profile_comments":
            user = User.query.filter_by(id=id).first()
            comment = user.comment
            return comment
    user_id = get_jwt_identity()["user_id"]
    user = User.query.filter_by(id=id).first()
    post_id = user.post_seen
    value_id = []
    for i in post_id:
        value_id.append(i.id)
    return Post.query.order_by(Post.date.desc()).where(~Post.id.in_(value_id)).offset(offset).limit(limit).all()


def follow(user_id, follow_id):
    user = User.query.filter_by(id=user_id).first()
    following = User.query.filter_by(id=follow_id).first()
    if following in user.following:
        db.session.commit()
        return user
    user.following.append(following)
    user.count_of_following += 1
    following.followers += 1
    db.session.commit()
    return user


def unfollow(user_id, follow_id):
    user = User.query.filter_by(id=user_id).first()
    following = User.query.filter_by(id=follow_id).first()
    if following not in user.following:
        return user
    user.following.remove(following)
    user.count_of_following -= 1
    following.followers -= 1
    db.session.commit()
    return user


def add_post(user_id, text, tags):
    date = time_now()
    post = Post(text, date, user_id)
    db.session.add(post)
    for i in tags:
        if Tags.query.filter_by(text=i).first():
            continue
        tag = Tags(i)
        db.session.add(tag)
    post = db.session.query(Post).order_by(Post.id.desc()).where(Post.author == user_id).first()
    for i in tags:
        tag = Tags.query.filter_by(text=i).first()
        post.tags.append(tag)
    db.session.commit()
    return post


def add_reaction(user_id, select, selection_id, reaction):
    if select == "post":
        post = Post.query.filter_by(id=selection_id).first()
        query = db.session.query(user_post_likes). \
            filter(user_post_likes.c.post_id == selection_id, user_post_likes.c.user_id == user_id)
        user = User.query.filter_by(id=user_id).first()
        user.user_post_likes.append(post)
        if not query.first():
            db.session.commit()
        query.update({user_post_likes.c.reaction: reaction})
        db.session.commit()
        return post
    else:
        comment = Comment.query.filter_by(id=selection_id).first()
        post = Post.query.filter_by(id=comment.post_id).first()
        query = db.session.query(user_comment_likes). \
            filter(user_comment_likes.c.comment_id == selection_id, user_comment_likes.c.user_id == user_id)
        user = User.query.filter_by(id=user_id).first()
        user.user_comment_likes.append(comment)
        if not query.first():
            db.session.commit()
        query.update({user_comment_likes.c.reaction: reaction})
        db.session.commit()
        return post


def delete_reaction(user_id, select, selection_id):
    if select == "post":
        reaction = User.query.filter_by(id=user_id).first()
        post_id = Post.query.filter_by(id=selection_id).first()
        reaction.user_post_likes.remove(post_id)
        db.session.commit()
        return post_id
    else:
        comment = Comment.query.filter_by(id=selection_id).first()
        post = Post.query.filter_by(id=comment.post_id).first()
        reaction = User.query.filter_by(id=user_id).first()
        reaction.user_comment_likes.remove(comment)
        db.session.commit()
        return post


def delete_post(post_id):
    post = db.session.query(Post).filter_by(id=post_id).first()
    post.likes.clear()
    post.tags.clear()
    post.comment.clear()
    db.session.delete(post)
    db.session.commit()


def delete_user(user_id, delete):
    user = User.query.filter_by(id=user_id).first()
    user.deleted = delete
    db.session.commit()

def add_commet(user_id, text, post_id):
    date = time_now()
    comment = Comment(text, post_id, user_id, date)
    db.session.add(comment)
    db.session.commit()
    return Post.query.filter_by(id=post_id).first()


def delete_comment(comment_id, post_id):
    comment = db.session.query(Comment).filter_by(id=comment_id).first()
    db.session.delete(comment)
    db.session.commit()
    return Post.query.filter_by(id=post_id).first()


def seen(user_id, post_id):
    user = User.query.filter_by(id=user_id).first()
    for i in post_id:
        post = Post.query.filter_by(id=i).first()
        user.post_seen.append(post)
        db.session.commit()