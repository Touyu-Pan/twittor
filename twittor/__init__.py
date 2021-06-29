from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from twittor.config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'login'

from twittor.route import index, login, logout, register, user, page_not_found, edit_profile

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    app.add_url_rule('/index', 'index', index, methods=['GET', 'POST'])
    app.add_url_rule('/', 'index', index, methods=['GET', 'POST'])
    app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
    app.add_url_rule('/logout', 'logout', logout)
    app.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
    app.add_url_rule('/<username>', 'profile', user, methods=['GET', 'POST'])
    app.register_error_handler(404, page_not_found)
    app.add_url_rule('/edit_profile', 'edit_profile', edit_profile, methods=['GET', 'POST'])
    return app
    