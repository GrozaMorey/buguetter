from flask import render_template, request, Response, jsonify, make_response, redirect
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, create_refresh_token, get_jwt, \
    set_refresh_cookies, set_access_cookies, unset_access_cookies, unset_jwt_cookies
from defs import *
from app import jwt, app, logger
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
            if jti in i.jwt:
                return True
    return False

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

# TODO: Включить ssl_context='adhoc' перед деплоем
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
