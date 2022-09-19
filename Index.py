from flask import Flask,render_template,url_for, request, redirect, flash
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
    login = db.Column(db.String(40), nullable= False)
    name = db.Column(db.String(40), nullable=False)
    password = db.Column(db.String(255), nullable= False)

    def __init__(self, login, name, password):
        self.login = login
        self.name = name
        self.password = password


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

@app.route("/index", methods=['POST', 'GET'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == "POST" and 'login' in request.form and 'name' in request.form and 'password' in request.form:
        name = request.form['name']
        login = request.form['login']
        password = request.form['password']
        session['username'] = request.form['name']

        _hashed_password = generate_password_hash(password)

        cursor.execute(f"SELECT * FROM {DB_TABLE} WHERE login = '%s'" % login)
        account = cursor.fetchone()
        if account:
            flash('Такой акк уже есть')
        else:

            cursor.execute(f"INSERT INTO {DB_TABLE} (login, name, password) VALUES (%s,%s,%s)", (login, name, _hashed_password))
            conn.commit()
            flash("эЭЭ я тЕбя Зарегал жи ест")


    return render_template("index.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
