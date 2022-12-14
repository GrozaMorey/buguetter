from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
from loguru import logger


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
db_config = {
    "DB_HOST": os.environ.get('DB_HOST'),
    "DB_NAME": os.environ.get('DB_NAME'),
    "DB_USER": os.environ.get('DB_USER'),
    "DB_PASS": os.environ.get('DB_PASS'),
    "DB_PORT": os.environ.get('DB_PORT'),
    "DB_TABLE": os.environ.get('DB_TABLE'),
}


logger.add("debug.log", format="{time} {level} {message}", level="DEBUG")


app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config['BASE_URL'] = 'http://127.0.0.1:5000'
app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://{db_config["DB_USER"]}:{db_config["DB_PASS"]}@{db_config["DB_HOST"]}/{db_config["DB_NAME"]}'
app.config["JWT_SECRET_KEY"] = "LKSDGKL:SD"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=999)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
# TODO: Сдеалть https хотя бы в этом столетии
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
jwt = JWTManager(app)

post_tags = db.Table('post_tags',
                     db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                     db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
                     )


user_post = db.Table("user_post",
                     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                     db.Column('date', db.Integer)
                     )


user_post_likes = db.Table("user_post_likes",
                     db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
                     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('reaction', db.String)
                     )


user_tags = db.Table("user_tags",
                     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
                     db.Column('karma_tag', db.Integer, default=0)
                     )


user_user_following = db.Table("user_user_following",
                     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('following_user_id', db.Integer, db.ForeignKey('users.id'))
                               )


user_comment_likes = db.Table("user_comment_likes",
                     db.Column('comment_id', db.Integer, db.ForeignKey('comment.id')),
                     db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                     db.Column('reaction', db.String)
                     )

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(40), nullable=False)
    name = db.Column(db.String(40), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    followers = db.Column(db.Integer, default=0)
    count_of_following = db.Column(db.Integer, default=0)
    deleted = db.Column(db.Boolean, default=False)
    date = db.Column(db.Integer)
    post = db.relationship('Post', backref='post')
    jwt = db.relationship('Jwt', backref='black_jwt')
    post_seen = db.relationship('Post', secondary=user_post, backref="user")
    user_tags = db.relationship('Tags', secondary=user_tags, backref="tags")
    following = db.relationship('User', secondary=user_user_following,
                                primaryjoin=(user_user_following.c.user_id == id),
                                secondaryjoin=(user_user_following.c.following_user_id == id),
                                backref="follower")
    comment = db.relationship('Comment', backref='comment_user_id')
    user_post_likes = db.relationship('Post', secondary=user_post_likes, backref="user_likes")
    user_comment_likes = db.relationship('Comment', secondary=user_comment_likes, backref="user_likes_comment")

    def __init__(self, login, name, password, date):
        self.login = login
        self.name = name
        self.password = password
        self.date = date


class Jwt(db.Model):
    __tablename__ = "invalid_tokens"
    id = db.Column(db.Integer, primary_key=True)
    jwt = db.Column(db.String, nullable=False)
    date = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, jwt, date, user_id):
        self.jwt = jwt
        self.date = date
        self.user_id = user_id


class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1000), nullable=False)
    date = db.Column(db.Integer)
    author = db.Column(db.Integer, db.ForeignKey('users.id'))
    cool = db.Column(db.Integer)
    shit = db.Column(db.Integer)
    angry = db.Column(db.Integer)
    nice = db.Column(db.Integer)
    popularity = db.Column(db.Integer)
    karma = db.Column(db.Integer)
    total = db.Column(db.Integer)
    tags = db.relationship('Tags', secondary=post_tags, backref="taged")
    comment = db.relationship('Comment', backref='comment_post_id')
    likes = db.relationship('User', secondary=user_post_likes, backref="post_likes")

    def __init__(self, text, date, author):
        self.text = text
        self.date = date
        self.author = author
        self.cool = 0
        self.shit = 0
        self.angry = 0
        self.nice = 0
        self.popularity = 0
        self.karma = 0
        self.total = 0


class Tags(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)

    def __init__(self, text):
        self.text = text


class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.Integer)
    likes = db.relationship('User', secondary=user_comment_likes, backref="user_like")

    def __init__(self, text, post_id, author_id, date):
        self.text = text
        self.post_id = post_id
        self.author_id = author_id
        self.date = date


