# buguetter backend api
Что делать если ты фронтедщик и попал сюда.  

Пулишь последнюю версию

Заходишь в app.py и меняешь app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:123@localhost/User" на "postgresql://postgres:пароль@localhost/имя 
бд(по дефолту postgres)"

Запускаешь Pgadmin 4 

Заходишь в терминал и вводишь команды 

flask db stump head 

flask db upgrade

Запускаешь index.py и далее следуешь схеме
