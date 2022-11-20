# buguetter backend api
Что делать если ты фронтедщик и попал сюда.  

Пулишь последнюю версию

Заходишь в `app.py` и меняешь  
`app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:123@localhost/User"` на  
`"postgresql://postgres:пароль@localhost/имя_бд`"  

Запускаешь Pgadmin 4 

Заходишь в терминал и вводишь команды 
```bash
flask db init
flask db migrate
flask db upgrade
```
Запускаешь `index.py` и далее следуешь схеме
////////////////////////////////////////////////////////////////////////////////////////////

Stack:
Flask
Flask-SQLALCHEMY
Flask-JWT-Extended
Flask-Migrate
Loguru
Postgresql
Strawberry GraphQL

