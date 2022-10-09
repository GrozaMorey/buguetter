from flask import render_template, request, Response
from flask import jsonify, make_response, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token, get_jwt, \
    set_refresh_cookies, set_access_cookies, unset_access_cookies, unset_jwt_cookies
from defs import *
from db_script import db_script
from app import jwt, app
from hype import hype, reactio
import json


@jwt.expired_token_loader
def expired_token_callback(x, z):
    return redirect(app.config['BASE_URL'] + '/api/refresh')


@jwt.revoked_token_loader
def revoked_callback(x, z):
    return jsonify({"error": 10})


@jwt.invalid_token_loader
def invalid_token_callback(x, z):
    return jsonify({"error": 9})


@jwt.unauthorized_loader
def unauthorized_loader_callback(x):
    return jsonify({"error": 8})


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

        account = cursor_select("login", login)
        if account is not None:
            if check_password_hash(account[-1], password) is True:
                token = create_access_token(identity=account[0])
                refresh_token = create_refresh_token(identity=account[0])

                response = make_response(jsonify({"msg": "success"}))
                set_refresh_cookies(response, refresh_token, max_age=2592000)
                set_access_cookies(response, token, max_age=2592000)
                return response
            else:
                return jsonify({"error": 3})
        else:
            return jsonify({"error": 2})
    return jsonify({"error": 1})


@app.route("/api/register", methods=['POST', 'GET'])
def register():
    # Собирание данные с форм и хеширование паса
    if request.method == "POST" and 'login' in request.json and 'name' in request.json and 'password' in request.json:
        name = request.json['name']
        login = request.json['login']
        password = request.json['password']

        _hashed_password = generate_password_hash(password)

        # Проверка на валидность имени и логина
        account = cursor_select("login", login)
        if account:
            return jsonify({"error": 4})
        account = cursor_select("name", name)
        if account:
            return jsonify({"error": 5})

            # Занос в бд
        try:
            add_user(login, name, _hashed_password)
            return {"response": True}
        except Exception as e:
            print(e)
            return jsonify({"error": 6})


@app.route("/api/protect", methods=['POST'])
@jwt_required()
def protect():
    current_user = get_jwt_identity()
    return jsonify(current_user)


@app.route('/api/refresh', methods=['GET'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    response = make_response(jsonify({"msg": "new_token"}))
    unset_access_cookies(response)
    set_access_cookies(response, access_token, max_age=2592000)

    return response


@app.route("/api/logout", methods=["DELETE"])
@jwt_required(refresh=True)
def logout():
    token = get_jwt()["jti"]
    print(token)
    token_exp = get_jwt()["exp"]
    user_id = get_jwt_identity()
    try:
        add_token_blacklist(token, token_exp, user_id)
        response = make_response({"msg": "success"})
        unset_jwt_cookies(response)
        return response
    except Exception as e:
        print(e)
        return jsonify({"error": 6})


@app.route("/api/status", methods=["GET"])
def status():
    return {"status": check_db()}


@app.route("/db")
def db():
    db_script()
    return "good"


@app.route("/api/publish_post", methods=["POST"])
@jwt_required()
def publish_post():
    if request.method == "POST" and 'text' in request.json and 'tags' in request.json:
        user_id = get_jwt_identity()
        text = request.json["text"]
        tags = request.json["tags"]
        add_post(text, user_id, tags)
        return {"response": True}
    return jsonify({"error": 7})


@app.route("/api/add_tags", methods=["POST"])
@jwt_required()
def add_tags():
    if request.method == "POST" and "text" in request.json:
        text = request.json["text"]
        add_tag(text, )
        return {"response": True}
    return {"response": True}


@app.route("/api/add_reaction", methods=["POST"])
@jwt_required()
def add_reactions():
    if request.method == "POST" and 'post_id' in request.json and 'reactions' in request.json:
        post_id = request.json["post_id"]
        reactions = request.json["reactions"]
        user_id = get_jwt_identity()

        add_reaction(post_id, reactions, user_id)
        return {"response": True}
    return {"response": False}


@app.route("/api/feed", methods=["POST"])
@jwt_required()
def feed():
    user_id = get_jwt_identity()
    post_id = request.json["post_id"]
    response = Response(json.dumps(get_feed(post_id, user_id)), mimetype='application/json')
    return response


@app.route("/api/get_user_data", methods=["POST"])
@jwt_required()
def get_user_data():
    user_id = get_jwt_identity()
    return {"name": f"{get_user_data(user_id)}"}


# TODO: Включить ssl_context='adhoc' перед деплоем
if __name__ == "__main__":
    app.run(debug=True)
