import typing
import strawberry
from app import jwt_required, get_jwt_identity, app
from defs import *
import requests
from flask import request

@strawberry.type
class User_data:
    user_id: int
    username: str
    following: int
    follow: int


@strawberry.type
class Check:
    status: str

@jwt_required()
def get_user(user_name: str):
    if user_name == "me":
        user_name = get_jwt_identity()["username"]
    return [User_data(
        user_id=get_user_id(user_name),
        username=get_user_name(user_name),
        following=get_user_following(user_name),
        follow=get_user_follow(user_name)
    )]

def check():
    status = requests.get(app.config['BASE_URL'] + '/api/protect', cookies={"access_token_cookie": request.cookies.get("access_token_cookie")}).text
    return Check(
        status= "token is valid"
    )



@strawberry.type
class Query:
    user_data: typing.List[User_data] = strawberry.field(resolver=get_user)
    check: Check = strawberry.field(resolver=check)


schema = strawberry.Schema(query=Query)