from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import psycopg2.extras
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, create_refresh_token, \
    get_jwt
from datetime import timedelta
import defs
from db_script import db_script


app = Flask(__name__)
db = SQLAlchemy(app)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config["JWT_SECRET_KEY"] = "LKSDGKL:SD"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
jwt = JWTManager(app)

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

@jwt.token_in_blocklist_loader
def check_token_blocklist(jwt_headers, jwt_data):
    jti = jwt_data["jti"]
    tokens = get_blocklist_db()
    for i in tokens:
        if jti in i["jti"]:
            return True
    return False


@app.route('/')
def index():
    return render_template("index.html")


@app.route("/api/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST' and 'login' in request.json and 'password' in request.json:
        login = request.json['login']
        password = request.json['password']
        users = get_users()

        for i in users:
            if i['login'] == login and check_password_hash(i["password"], password) is True:
                token = create_access_token(identity=i['id'])
                refresh_token = create_refresh_token(identity=i['id'])
                return {'token': token, "refresh_token": refresh_token}
        else:
            return {"response": False}

    return 'hh'


@app.route("/api/register", methods=['POST', 'GET'])
def register():
    # Собирание данные с форм и хеширование паса
    if request.method == "POST" and 'login' in request.json and 'name' in request.json and 'password' in request.json:
        get_users()
        name = request.json['name']
        login = request.json['login']
        password = request.json['password']

        _hashed_password = generate_password_hash(password)

        # Проверка на валидность имени и логина

        data_response = {
            "response": True
        }
        account = cursor_select("login", login)
        if account:
            data_response['response'] = "Куда лезешь он уже есть"
            return data_response

        account = cursor_select("name", name)
        if account:
            data_response['response'] = "Такое имя уже есть "
            return data_response
        else:

            # Занос в бд
            add_user(login, name, _hashed_password)
            return data_response

    return render_template("index.html")


@app.route("/api/protect", methods=['POST'])
@jwt_required()
def protect():
    current_user = get_jwt_identity()
    return jsonify(current_user)


@app.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token})


@app.route("/api/logout", methods=["DELETE"])
@jwt_required(verify_type=False)
def logout():
    token = get_jwt()["jti"]
    token_exp = get_jwt()["exp"]
    add_token_blacklist(token, token_exp)
    return {"response": "success"}

@app.route("/api/status", methods=["GET"])
def status():
    return {"status": True}

@app.route("/db")
def db():
    db_script()
    return "good"

if __name__ == "__main__":
    app.run(debug=True)
