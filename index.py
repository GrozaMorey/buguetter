from flask import render_template, request, Response, jsonify, make_response, redirect
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token, get_jwt, \
    set_refresh_cookies, set_access_cookies, unset_access_cookies, unset_jwt_cookies
from defs import *
from db_script import db_script
from app import jwt, app, logger
from hype import hype, reactio
import json
from strawberry.flask.views import GraphQLView
from schema import schema


@jwt.expired_token_loader
def expired_token_callback(x, jwt):
    logger.info("expired jwt loader run")
    if jwt["type"] == "refresh":
        return False
    else:
        request_refresh = requests.get(app.config['BASE_URL'] + '/api/refresh', cookies={"refresh_token_cookie": request.cookies.get("refresh_token_cookie")})
        response = make_response(request_refresh.json())
        if not request_refresh.cookies:
            response = make_response(jsonify({"msg": "error", "error": 16}))
            unset_jwt_cookies(response)
            return response
        cookie = request_refresh.cookies["access_token_cookie"]
        set_access_cookies(response, cookie, max_age=2592000)
        return response


@jwt.revoked_token_loader
def revoked_callback(x, z):
    logger.info("revoked jwt loader run")
    return jsonify({"msg": "error", "error": 9})


@jwt.invalid_token_loader
def invalid_token_callback(x, z):
    logger.info("invalid jwt loader run")
    return jsonify({"msg": "error", "error": 8})


@jwt.unauthorized_loader
def unauthorized_loader_callback(x):
    logger.info("unauthorized jwt loader run")
    response = jsonify({"msg": "error", "error": 7})
    unset_jwt_cookies(response)
    return response


@jwt.token_in_blocklist_loader
def check_token_blocklist(jwt_headers, jwt_data):
    logger.info("blacklist jwt loader run")
    jti = jwt_data["jti"]
    tokens = get_blocklist_db()
    if tokens is not None:
        for i in tokens:
            if jti in i["jti"]:
                return True
    return False

def graphql_token_view():
    view = GraphQLView.as_view('graphql', schema=schema)
    view = jwt_required()(view)
    return view

app.add_url_rule(
    "/graphql",
    view_func=graphql_token_view())

@app.route('/')
def index():
    return render_template("index.html")


@app.route("/api/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST' and 'login' in request.json and 'password' in request.json:
        logger.info("login get data")
        login = request.json['login']
        password = request.json['password']

        account = cursor_select("login", login)
        if account is not None:
            if check_password_hash(account[-3], password) is True:
                identify = {
                    "user_id":account[0],
                    "username": account[1]
                }
                token = create_access_token(identity=identify)
                refresh_token = create_refresh_token(identity=identify)

                response = make_response(jsonify({"msg": "success", "error": 0}))
                set_refresh_cookies(response, refresh_token, max_age=2592000)
                set_access_cookies(response, token, max_age=2592000)
                logger.info("login success")
                return response
            else:
                logger.info("login wrong password")
                return jsonify({"msg": "error", "error": 3})
        else:
            logger.info("login wrong login")
            return jsonify({"msg": "error", "error": 2})
    logger.info("login data is null")
    return jsonify({"msg": "error", "error": 1})


@app.route("/api/register", methods=['POST', 'GET'])
def register():
    # Собирание данные с форм и хеширование паса
    if request.method == "POST" and 'login' in request.json and 'name' in request.json and 'password' in request.json:
        logger.info("register get data")
        name = request.json['name']
        login = request.json['login']
        password = request.json['password']

        _hashed_password = generate_password_hash(password)

        # Проверка на валидность имени и логина
        account = cursor_select("login", login)
        if account:
            logger.info("register login already used")
            return jsonify({"msg": "error", "error": 4})
        account = cursor_select("name", name)
        if account:
            logger.info("register name already used")
            return jsonify({"msg": "error", "error": 5})

            # Занос в бд

        add_user(login, name, _hashed_password)
        logger.info("register success")
        logger.info("register success")
        return jsonify({"msg": "success", "error": 0})


@app.route("/api/protect", methods=['GET'])
@jwt_required()
def protect():
    logger.info("protect run")
    current_user = get_jwt_identity()
    return jsonify(current_user)


@app.route('/api/refresh', methods=['GET'])
@jwt_required(refresh=True)
def refresh():
    if request.method == "OPTIONS":
        print("dsfsd")
    logger.info("refresh run")
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    graphql_answer = {
    "data": {
        "check": {
            "status": "refreshed your ass boy"
        }
    }
}
    response = make_response(graphql_answer)
    set_access_cookies(response, access_token)

    return response


@app.route("/api/logout", methods=["DELETE"])
@jwt_required(refresh=True)
def logout():
    logger.info("logout run")
    token = get_jwt()["jti"]
    token_exp = get_jwt()["exp"]
    user_id = get_jwt_identity()
    try:
        logger.info("try add token to blacklist run")
        add_token_blacklist(token, token_exp, user_id)
        response = make_response(jsonify({"msg": "success", "error": 0}))
        unset_jwt_cookies(response)
        logger.info("logout success")
        return response
    except:
        logger.error("logout error")
        return jsonify({"msg": "error", "error": 6})


@app.route("/api/status", methods=["GET"])
def status():
    logger.info("status run")
    status = check_db()
    if status is not True:
        return jsonify({"msg": "error", "error": 13})
    return jsonify({"msg": "success", "error": 0})


@app.route("/db")
def db():
    db_script()
    return "good"


@app.route("/api/publish_post", methods=["POST"])
@jwt_required()
def publish_post():
    logger.info("publish post run")
    try:
        if request.method == "POST" and 'text' in request.json and 'tags' in request.json:
            logger.info("publish post get data")
            user_id = get_jwt_identity()
            text = request.json["text"]
            tags = request.json["tags"]
            post = add_post(text, user_id, tags)
            if post is not True:
                return jsonify({"msg": "error", "error": 12})
            logger.info("publish post success")
            return jsonify({"msg": "success", "error": 0})
        logger.info("publish post data is null")
    except Exception as e:
        logger.error(f"publish post error {e}")
        return jsonify({"msg": "error", "error": 6})


@app.route("/api/add_reaction", methods=["POST"])
@jwt_required()
def add_reactions():
    logger.info("add reaction run")
    if request.method == "POST" and 'post_id' in request.json and 'reactions' in request.json:
        logger.info("add reaction get data ")
        post_id = request.json["post_id"]
        reactions = request.json["reactions"]
        user_id = get_jwt_identity()
        add_reaction(post_id, reactions, user_id)
        logger.info("add reaction success")
        return jsonify({"msg": "success"})
    logger.info("add reaction data is null")
    return jsonify({"msg": "error", "error": 11})


@app.route("/api/feed", methods=["POST", "GET"])
@jwt_required()
def feed():
    logger.info("feed run")
    user_id = get_jwt_identity()
    post_id = request.json["post_id"]
    response = Response(json.dumps(get_feed(post_id, user_id)), mimetype='application/json')
    logger.info("feed success")
    return response


@app.route("/api/get_user_data", methods=["GET"])
@jwt_required()
def return_user_data():
    logger.info("get user data run")
    user_id = get_jwt_identity()
    user_name = get_user_data(user_id)
    logger.info("get user data success")
    return user_name


@app.route("/api/get_user_post", methods=["POST"])
@jwt_required()
def get_user_post():
    logger.info("get user post run")
    user_id = request.json["user_id"]
    request_user_id = get_jwt_identity()
    post = get_post_user(user_id, request_user_id)
    logger.info("get user post success")
    return post


@app.route("/api/get_user_like", methods=["POST"])
@jwt_required()
def get_user_like():
    logger.info("get user like run")
    user_id = request.json["user_id"]
    post = get_likes(user_id)
    logger.info("get user like success")
    return post


@app.route("/api/get_another_user", methods=["POST"])
@jwt_required()
def get_another_user():
    logger.info("get another user run")
    name = request.json["name"]
    result = get_another_user_data(name)
    logger.info("get another user success")
    return result


@app.route("/api/delete_account", methods=["DELETE"])
@jwt_required()
def delete_account_route():
    logger.info("delete account like run")
    user_id = get_jwt_identity()
    delete_account(user_id)
    logger.info("delete account success")
    return {"msg": "success", "error": 0}


@app.route("/api/delete_post", methods=["DELETE"])
@jwt_required()
def delete_post_route():
    logger.info("delete post run")
    post_id = request.json["post_id"]
    delete_post(post_id)
    logger.info("delete post success")
    return {"msg": "success", "error": 0}


@app.route("/api/delete_like", methods=["DELETE"])
@jwt_required()
def delete_like_route():
    logger.info("delete like run")
    post_id = request.json["post_id"]
    user_id = get_jwt_identity()
    delete_like(user_id, post_id)
    logger.info("delete like success")
    return {"msg": "success", "error": 0}


@app.route("/api/follow", methods=["POST"])
@jwt_required()
def follow_route():
    logger.info("follow run")
    follow_id = request.json["follow_id"]
    user_id = get_jwt_identity()
    follow(user_id, follow_id)
    logger.info("follow success")
    return {"msg": "success", "error": 0}


@app.route("/api/add_comment", methods=["POST"])
@jwt_required()
def add_comment_route():
    logger.info("add comment run")
    text = request.json["text"]
    post_id = request.json["post_id"]
    user_id = get_jwt_identity()
    add_comment(text, post_id, user_id)
    logger.info("add comment success")
    return {"msg": "success", "error": 0}


@app.route("/api/get_comment", methods=["POST"])
@jwt_required()
def get_comment_route():
    logger.info("get comment run")
    post_id = request.json["post_id"]
    response = get_comment(post_id)
    logger.info("get comment success")
    return response


@app.route("/api/unfollow", methods=["DELETE"])
@jwt_required()
def unfollow_route():
    logger.info("unfollow run")
    follow_id = request.json["follow_id"]
    user_id = get_jwt_identity()
    unfollow(user_id, follow_id)
    logger.info("unfollow success")
    return {"msg": "success", "error": 0}

# TODO: Включить ssl_context='adhoc' перед деплоем
if __name__ == "__main__":
    app.run(debug=True)
