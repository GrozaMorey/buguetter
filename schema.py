import strawberry
from app import db, user_post_likes, Post, User, Tags
from defs import jwt_required, get_jwt_identity, get_jwt, register,\
    add_token_blacklist, create_access_token, time_now, loging
from typing import Union, Optional, List
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
                user = User.query.filter_by(id=id).first()
                return user.user_post_likes
            case "profile_comments":
                user = User.query.filter_by(id=id).first()
                comment = user.comment
                return comment
        user_id = get_jwt_identity()["user_id"]
        user = db.session.query(User).filter(id == user_id).first()
        post_id = user.post_seen
        value_id = []
        for i in post_id:
            value_id.append(i.id)
        return Post.query.order_by(Post.date.desc()).where(~Post.id.in_(value_id)).offset(offset).limit(limit).all()


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
    def register(self,login: str, name: str, password: str) -> Union[Status, Users_Realationship]:
        if register(login, name, password) is False:
            return Status(msg="error", error="1")
        user = User.query.filter_by(login=login).first()
        return Users_Realationship(id=user.id, name=user.name, date=user.date, follower=user.follower,
                                   following=user.following)


    @strawberry.field
    def login(self, login: str, password: str, info:Info) -> Union[Status, Users_Realationship]:
        tokens = loging(login, password)
        if len(tokens) == 3:
            return Status(msg=tokens["msg"], error=tokens["error"])
        info.context["response"].set_cookie(key="access_token_cookie", value=tokens[0], max_age=2592000, httponly=True)
        info.context["response"].set_cookie(key="refresh_token_cookie", value=tokens[1], max_age=2592000, httponly=True)
        user = User.query.filter_by(login=login).one()
        return Users_Realationship(id=user.id, name=user.name, date=user.date,
                                   follower=user.follower, following=user.following)

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
        info.context["response"].set_cookie(key="access_token_cookie", value=access_token,
                                            max_age=2592000, httponly=True)
        return Status(msg="success", error=0)

    @strawberry.field
    @jwt_required()
    def seen(self, post_id: List[int]) -> Status:
        user_id = get_jwt_identity()["user_id"]
        user = User.query.filter_by(id=user_id).first()
        for i in post_id:
            post = Post.query.filter_by(id=i).first()
            user.post_seen.append(post)
            db.session.commit()
        return Status(msg="success", error=0)

    @strawberry.field
    @jwt_required()
    def follow(self, follow_login: str) -> Users_Realationship:
        user_id = get_jwt_identity()["user_id"]
        user = User.query.filter_by(id=user_id).first()
        following = User.query.filter_by(login=follow_login).first()
        if following in user.following:
            db.session.commit()
            return user
        user.following.append(following)
        user.count_of_following += 1
        following.followers += 1
        db.session.commit()
        return user

    @strawberry.field
    @jwt_required()
    def unfollow(self, follow_login: str) -> Users_Realationship:
        user_id = get_jwt_identity()["user_id"]
        user = User.query.filter_by(id=user_id).first()
        following = User.query.filter_by(login=follow_login).first()
        if following not in user.following:
            return user
        user.following.remove(following)
        user.count_of_following -= 1
        following.followers -= 1
        db.session.commit()
        return user

    @strawberry.field
    @jwt_required()
    def add_post(self, text: str, tags: Optional[List[str]]) -> Posts:
        user_id = get_jwt_identity()["user_id"]
        date = time_now()
        post = Post(text, date, user_id)
        db.session.add(post)
        for i in tags:
            if Tags.query.filter_by(text=i).first():
                continue
            tag = Tags(i)
            db.session.add(tag)
        post = db.session.query(Post).order_by(Post.id.desc()).where(Post.author == user_id).first()
        for i in tags:
            tag = Tags.query.filter_by(text=i).first()
            post.tags.append(tag)
        db.session.commit()

        return post

    @strawberry.field
    @jwt_required()
    def add_reaction(self, reaction: str, post_id: int) -> Posts:
        user_id = get_jwt_identity()["user_id"]
        query = db.session.query(user_post_likes).\
            filter(user_post_likes.c.post_id == post_id, user_post_likes.c.post_id == post_id)
        post = Post.query.filter_by(id=post_id).first()
        user = User.query.filter_by(id=user_id).first()
        user.user_post_likes.append(post)
        if not query.first():
            db.session.commit()
        query.update({user_post_likes.c.reaction: reaction})
        db.session.flush()
        db.session.commit()
        post = Post.query.filter_by(id=post_id).first()
        return post

    @strawberry.field
    @jwt_required()
    def delete_reaction(self, post_id: int) -> Posts:
        user_id = get_jwt_identity()["user_id"]
        reaction = User.query.filter_by(id=user_id).first()
        post_id = Post.query.filter_by(id=post_id).first()
        reaction.user_post_likes.remove(post_id)
        db.session.commit()
        return Post.query.filter_by(id=post_id).first()

    @strawberry.field
    @jwt_required()
    def delete_post(self, post_id: int) -> Status:
        post = db.session.query(Post).filter_by(id=post_id).first()
        post.likes.clear()
        post.tags.clear()
        post.comment.clear()
        db.session.delete(post)
        db.session.commit()
        return Status(msg="success", error=0)

    @strawberry.field
    @jwt_required()
    def delete_user(self, delete: bool) -> Status:
        user_id = get_jwt_identity()["user_id"]
        user = User.query.filter_by(id=user_id).first()
        user.deleted = delete
        db.session.commit()
        return Status(msg="success", error=0)


schema = strawberry.Schema(query=Query, mutation=Mutation)
