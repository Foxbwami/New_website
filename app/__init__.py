from flask import Flask
from flask_mail import Mail
from app.extensions import db, login_manager, migrate
from app.models import User
from flask_login import current_user

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    login_manager.init_app(app)
    # Optional inline overrides
    app.config['SECRET_KEY'] = 'bwami123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your.db'

    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'bwamistevenez001@gmail.com'
    app.config['MAIL_PASSWORD'] = 'bwami123'
    app.config['MAIL_DEFAULT_SENDER'] = 'littlefox007j@gmail.com'

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app  # ✅ this must be inside the create_app() function
