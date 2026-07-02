"""Application factory and backward-compatible default application."""

from flask import Flask

from app.extensions import babel, db, login_manager
from config import Config


def create_app(config=None, *, register_admin=True):
    """Create and configure an application instance."""
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    if config:
        flask_app.config.from_mapping(config)

    db.init_app(flask_app)
    babel.init_app(flask_app, locale_selector=lambda: "vi")
    login_manager.init_app(flask_app)

    from app.api import api
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(student_bp)
    flask_app.register_blueprint(api)

    # Preserve the public endpoint names used by existing templates and
    # extensions while the owning view functions live inside blueprints.
    for rule, endpoint in (
        ("/", "login"),
        ("/logout", "logout"),
        ("/forgot-password", "forgot_password"),
        ("/index", "index"),
        ("/timetable", "timetable"),
        ("/study-result", "study_result"),
    ):
        flask_app.add_url_rule(rule, endpoint=endpoint, build_only=True)

    if register_admin:
        from app.admin import init_admin

        init_admin(flask_app)

    return flask_app


# Existing scripts import ``app`` directly. Keep one default instance while new
# code and tests can use ``create_app`` for isolated configuration.
app = create_app()


__all__ = ["app", "babel", "create_app", "db", "login_manager"]
