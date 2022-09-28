from flask import  render_template, request
from flask import jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token, get_jwt
from defs import *
from db_script import db_script
from app import jwt, app


# @jwt.token_in_blocklist_loader
# def check_token_blocklist(jwt_headers, jwt_data):
#     jti = jwt_data["jti"]
#     tokens = get_blocklist_db()
#     for i in tokens:
#         if jti in i["jti"]:
#             return True
#     return False


@app.route('/')
def index():
    return render_template("index.html")


@app.route("/api/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST' and 'login' in request.json and 'password' in request.json:
        login = request.json['login']
        password = request.json['password']

        account = cursor_select("login", login)
        if account is not None:
            if check_password_hash(account[-1], password) is True:
                token = create_access_token(identity=account[0])
                refresh_token = create_refresh_token(identity=account[0])
                return {'token': token, "refresh_token": refresh_token}
            else:
                return {"response": "wrong password"}
        else:
            return {"response": "none user"}





@app.route("/api/register", methods=['POST', 'GET'])
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

            # Занос в бд
        add_user(login, name, _hashed_password)
        return data_response




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
