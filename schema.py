import strawberry
from app import db, user_post_likes, Post, User, Tags, Comment, user_comment_likes
from defs import *
from typing import Optional, List
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
class Comments:
    id: int
    text: str
    post_id: int
    author_id: int
    date: int
    def get_relation_of_table(self):
        return db.session.query(user_comment_likes).join(Comment).filter_by(id=self.id).all()
    likes: List[Reaction] = strawberry.field(resolver=get_relation_of_table)


@strawberry.type
class Posts:
    id: int
    text: str
    date: int
    author: str
    comment: List[Comments]
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
        return feed(offset, limit, selection, id)


    @strawberry.field
    def status(self) -> Status:
        user = User.query.filter_by(id=1).first()
        if user:
            return Status(msg="success", error=0)


    @strawberry.field
    def find(self, id: int) -> Posts:
        return Post.query.filter_by(id=id).first()


@strawberry.type
class Mutation:
    @strawberry.field
    def register(self,login: str, name: str, password: str, info: Info) -> Users_Realationship:
        if register(login, name, password) is False:
            raise Exception("login already exists")
        tokens = loging(login, password)
        if len(tokens) != 2:
            raise Exception("incorrect login or password")
        info.context["response"].set_cookie(key="access_token_cookie", value=tokens[0], max_age=2592000, httponly=True)
        info.context["response"].set_cookie(key="refresh_token_cookie", value=tokens[1], max_age=2592000, httponly=True)
        user = User.query.filter_by(login=login).first()
        return user


    @strawberry.field
    def login(self, login: str, password: str, info: Info) -> Users_Realationship:
        tokens = loging(login, password)
        if len(tokens) != 2:
            raise Exception("incorrect login or password")
        info.context["response"].set_cookie(key="access_token_cookie", value=tokens[0], max_age=2592000, httponly=True)
        info.context["response"].set_cookie(key="refresh_token_cookie", value=tokens[1], max_age=2592000, httponly=True)
        user = User.query.filter_by(login=login).first()
        return user

    @strawberry.field
    @jwt_required(refresh=True)
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
        info.context["response"].set_cookie(key="access_token_cookie", value=access_token,
                                            max_age=2592000, httponly=True)
        return Status(msg="success", error=0)

    @strawberry.field
    @jwt_required()
    def seen(self, post_id: List[int]) -> Status:
        user_id = get_jwt_identity()["user_id"]
        seen(user_id, post_id)
        return Status(msg="success", error=0)

    @strawberry.field
    @jwt_required()
    def follow(self, follow_id: int) -> Users_Realationship:
        user_id = get_jwt_identity()["user_id"]
        return follow(user_id, follow_id)

    @strawberry.field
    @jwt_required()
    def unfollow(self, follow_id: int) -> Users_Realationship:
        user_id = get_jwt_identity()["user_id"]
        return unfollow(user_id, follow_id)

    @strawberry.field
    @jwt_required()
    def add_post(self, text: str, tags: Optional[List[str]]) -> Posts:
        user_id = get_jwt_identity()["user_id"]
        return add_post(user_id, text, tags)

    @strawberry.field
    @jwt_required()
    def add_reaction(self, reaction: str, selection_id: int, select: str) -> Posts:
        user_id = get_jwt_identity()["user_id"]
        return add_reaction(user_id, select, selection_id, reaction)

    @strawberry.field
    @jwt_required()
    def delete_reaction(self, selection_id: int, select: str) -> Posts:
        user_id = get_jwt_identity()["user_id"]
        return delete_reaction(user_id, select, selection_id)

    @strawberry.field
    @jwt_required()
    def delete_post(self, post_id: int) -> Status:
        delete_post(post_id)
        return Status(msg="success", error=0)

    @strawberry.field
    @jwt_required()
    def delete_user(self, delete: bool) -> Status:
        user_id = get_jwt_identity()["user_id"]
        delete_user(user_id, delete)
        return Status(msg="success", error=0)


    @strawberry.field
    @jwt_required()
    def add_comment(self, text: str, post_id: int) -> Posts:
        user_id = get_jwt_identity()["user_id"]
        return add_commet(user_id, text, post_id)

    @strawberry.field
    @jwt_required()
    def delete_comment(self, comment_id: int, post_id: int) -> Posts:
        return delete_comment(comment_id, post_id)


schema = strawberry.Schema(query=Query, mutation=Mutation)
