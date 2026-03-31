from flask import Flask
from flask_sqlalchemy import SQLAlchemy
<<<<<<< HEAD
from flask_login import login_manager
=======
>>>>>>> feature/admin



app = Flask(__name__)
<<<<<<< HEAD
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456@localhost/qldt_db?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "mfwkerh2i4or2ury2io3ry2oiftg3 iu4oteere"
db = SQLAlchemy(app=app)
##login=login_manager(app=app)
=======
app.secret_key = '3823%#^%#%#&(*&JHIUDGWO;DH'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:12345@localhost/qldt_db?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app=app)
>>>>>>> feature/admin
