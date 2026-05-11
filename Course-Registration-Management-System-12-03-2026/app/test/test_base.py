import pytest
from flask import Flask

from app import db
from app.utils import login_manager

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    app.config["SECRET_KEY"]= "4365ur76ifkyfvfytidyfyj"

    db.init_app(app)
    login_manager.init_app(app)

    from app import index as index_routes

    app.add_url_rule("/", "login", index_routes.login, methods=["GET", "POST"])

    return app

@pytest.fixture
def test_app():
    app = create_app()

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_session(test_app):
    yield db.session
    db.session.rollback()


@pytest.fixture
def test_client(test_app):
    return test_app.test_client()
