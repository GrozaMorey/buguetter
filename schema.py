import strawberry
from app import *
from defs import *
from typing import Union, Optional, Any, List
from strawberry.types import Info


@strawberry.type
class Users:
    id: int
    name: str
    date: int


@strawberry.type
class Status:
    msg: str
    error: int


@strawberry.type
class Reaction:
    user_id: int
    post_id: int
    reaction: str


@strawberry.type
class Comment:
    id: int
    text: str
    post_id: int
    author_id: int
    date: int


@strawberry.type
class Posts:
    id: int
    text: str
    date: int
    author: str
    comment: List[Comment]
    author_id: int
    post_id: int
    def get_relation_of_table(self):
        return db.session.query(user_post_likes).join(Post).filter_by(id=self.id).all()
    likes: List[Reaction] = strawberry.field(resolver=get_relation_of_table)


@strawberry.type
class Users_Realationship(Users):
    follower: List[Users]
    following: List[Users]


@strawberry.type
class Query:

    @strawberry.field
    @jwt_required()
    def user(self, id: int) -> Users_Realationship:
        if id == 0:
            id = get_jwt_identity()["user_id"]
        return User.query.filter_by(id=id).first()


    @strawberry.field
    @jwt_required()
    def feed(self, offset: int, limit: int, selection: str, id: Optional[int]) -> List[Posts]:
        if id == 0:
            id = get_jwt_identity()["user_id"]
        match selection:
            case "profile":
                return Post.query.filter_by(author=id).offset(offset).limit(limit).all()
            case "profile_likes":
                user = User.query.filter_by(id=id).one()
                return user.user_post_likes
            case "profile_comments":
                user = User.query.filter_by(id=id).one()
                comment = user.comment
                return comment
        return Post.query.order_by(Post.date.desc()).offset(offset).limit(limit).all()


    @strawberry.field
    def status(self) -> Status:
        user = User.query.filter_by(id=1).one()
        if user:
            return Status(msg="success", error=0)


    @strawberry.field
    def find(self, id: int) -> Posts:
        return Post.query.filter_by(id=id).one()


@strawberry.type
class Mutation:
    @strawberry.field
    def register(self,login: str, name: str, password: str) -> str:
        return register(login, name, password)


    @strawberry.field
    def login(self, login: str, password: str, info:Info) -> Status:
        tokens = loging(login, password)
        if len(tokens) == 3:
            return Status(msg=tokens["msg"], error=tokens["error"])
        info.context["response"].set_cookie(key="access_token_cookie", value=tokens[0], max_age=2592000, httponly=True)
        info.context["response"].set_cookie(key="refresh_token_cookie", value=tokens[1], max_age=2592000, httponly=True)
        return Status(msg="success", error=0)


    @strawberry.field
    @jwt_required()
    def logout(self, info: Info) -> Status:
        token = get_jwt()["jti"]
        token_exp = get_jwt()["exp"]
        user_id = get_jwt_identity()["user_id"]
        add_token_blacklist(token, token_exp, user_id)
        info.context["response"].set_cookie(key="access_token_cookie", value="", expires=0)
        info.context["response"].set_cookie(key="refresh_token_cookie", value="", expires=0)
        return Status(msg="success", error=0)


    @strawberry.field
    @jwt_required(refresh=True)
    def refresh(self, info: Info) -> Status:
        identity = get_jwt_identity()
        access_token = create_access_token(identity=identity)
        info.context["response"].set_cookie(key="access_token_cookie", value=access_token, max_age=2592000, httponly=True)
        return Status(msg="success", error=0)

schema = strawberry.Schema(query=Query, mutation=Mutation)