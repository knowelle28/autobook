from flask import Flask, session
from flask_login import LoginManager

from .models import db, User
from config import Config
from .i18n import TRANSLATIONS


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    from .booking import bp as booking_bp
    app.register_blueprint(booking_bp)

    from .admin import bp as admin_bp
    app.register_blueprint(admin_bp)

    # i18n context processor
    @app.context_processor
    def inject_i18n():
        lang = session.get('lang', 'en')
        strings = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
        def t(key):
            return strings.get(key, TRANSLATIONS['en'].get(key, key))
        return dict(t=t, lang=lang)

    # Create tables
    with app.app_context():
        db.create_all()

    return app
