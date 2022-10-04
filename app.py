from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
import os
from dotenv import load_dotenv

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



app = Flask(__name__)
CORS(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql://{db_config["DB_USER"]}:{db_config["DB_PASS"]}@{db_config["DB_HOST"]}/{db_config["DB_NAME"]}'
app.config["JWT_SECRET_KEY"] = "LKSDGKL:SD"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
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

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(40), nullable=False)
    name = db.Column(db.String(40), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    post = db.relationship('Post', backref='post')
    jwt = db.relationship('Jwt', backref='black_jwt')
    post_seen = db.relationship('Post', secondary=user_post, backref="user")

    def __init__(self, login, name, password):
        self.login = login
        self.name = name
        self.password = password


class Jwt(db.Model):
    __tablename__ = "invalid_tokens"
    id = db.Column(db.Integer, primary_key=True)
    jwt = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    cool = db.Column(db.Integer)
    shit = db.Column(db.Integer)
    angry = db.Column(db.Integer)
    popularity = db.Column(db.Integer)
    karma = db.Column(db.Integer)
    total = db.Column(db.Integer)
    tags = db.relationship('Tags', secondary=post_tags, backref="taged")

    def __init__(self, text, date, user_id):
        self.text = text
        self.date = date
        self.user_id = user_id
        self.cool = 0
        self.shit = 0
        self.angry = 0
        self.popularity = 0
        self.karma = 0
        self.total = 0


class Tags(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)

    def __init__(self, text):
        self.text = text


