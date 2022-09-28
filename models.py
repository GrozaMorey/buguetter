from app import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(40), nullable=False)
    name = db.Column(db.String(40), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __init__(self, login, name, password):
        self.login = login
        self.name = name
        self.password = password


class Jwt(db.Model):
    __tablename__ = "invalid_tokens"
    id = db.Column(db.Integer, primary_key=True)
    jwt = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)

    def __init__(self, jwt, date):
        self.jwt = jwt
        self.date = date