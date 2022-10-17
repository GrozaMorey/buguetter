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
class Users_Realationship(Users):
    follow: typing.List[Users]
    following: typing.List[Users]


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: int) -> Users_Realationship:
        return User.query.filter_by(id=id).first()




schema = strawberry.Schema(query=Query)