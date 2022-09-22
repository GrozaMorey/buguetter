from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import psycopg2.extras
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost/User'
db = SQLAlchemy(app)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

DB_HOST = "containers-us-west-53.railway.app"
DB_NAME = "railway"
DB_USER = "postgres"
DB_PASS = "WJk75v28XTSv2cczzwAN"
DB_PORT = "7193"
DB_TABLE = "users2"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)


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

def cursor_select(column, arg):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(f"SELECT * FROM {DB_TABLE} WHERE {column} = '{arg}'")
    account = cursor.fetchone()
    return account

def add_user(name,login,_hashed_password):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(f"INSERT INTO {DB_TABLE} (login, name, password) VALUES ('{name}','{login}','{_hashed_password}')")
    conn.commit()

@app.route('/')
def index():
    if 'username' in session:
        return f'Logged in as {session["username"]}'
    return 'You are not logged in'


@app.route("/login", methods=['POST', 'GET'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'login' in request.form and 'password' in request.form:
        login = request.form['login']
        password = request.form['password']

        cursor.execute(f"SELECT * FROM {DB_TABLE} WHERE login = '%s'" % login)
        account = cursor.fetchone()
        print(account)
    return render_template("login.html")


@app.route("/index", methods=['POST', 'GET'])
def register():


    # Собирание данные с форм и хеширование паса

    if request.method == "POST" and 'login' in request.json and 'name' in request.json and 'password' in request.json:
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
            add_user(name, login, _hashed_password)
            return data_response

    return render_template("index.html")


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
