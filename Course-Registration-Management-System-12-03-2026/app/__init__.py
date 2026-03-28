from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_manager



app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456@localhost/qldt_db?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app=app)
##login=login_manager(app=app)