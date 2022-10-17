import strawberry
from app import *
from defs import *
import typing



@strawberry.type
class Users:
    id: int
    name: str
    date: int

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
    comment: typing.List[Comment]
    author_id: int
    post_id: int
    def get_relation_of_table(self):
        return db.session.query(user_post_likes).join(Post).filter_by(id=self.id).all()
    likes: typing.List[Reaction] = strawberry.field(resolver=get_relation_of_table)


@strawberry.type
class Users_Realationship(Users):
    follower: typing.List[Users]
    following: typing.List[Users]


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: int) -> Users_Realationship:
        return User.query.filter_by(id=id).first()
    @strawberry.field
    def post(self, by: typing.Optional[str], id: typing.Optional[int]) -> typing.List[Posts]:
        match by:
            case "profile":
                return Post.query.filter_by(user_id=id).all()
            case "profile_likes":
                user = User.query.filter_by(id=id).one()
                return user.user_post_likes
            case "profile_comments":
                user = User.query.filter_by(id=id).one()
                comment = user.comment
                return comment
        return Post.query.order_by(Post.date.desc()).all()

    @strawberry.field
    def status(self) -> str:
        user = User.query.filter_by(id=1).one()
        if user:
            return "success"


schema = strawberry.Schema(query=Query)