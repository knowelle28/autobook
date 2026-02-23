from datetime import time as _time

from flask import Flask, session
from flask_login import LoginManager
from sqlalchemy import text

from .models import db, User
from config import Config
from .i18n import TRANSLATIONS


def _alter_tables():
    """Raw SQL: add schedule_type column to existing business_hours table if missing."""
    with db.engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='business_hours'")
        )
        if result.fetchone():
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(business_hours)"))]
            if 'schedule_type' not in cols:
                conn.execute(text(
                    "ALTER TABLE business_hours "
                    "ADD COLUMN schedule_type VARCHAR(20) NOT NULL DEFAULT 'regular'"
                ))
                conn.commit()


def _seed_schedule_rows():
    """ORM: ensure all 14 hour rows and the active_schedule setting exist."""
    from .models import BusinessHours, AppSetting

    if not AppSetting.query.get('active_schedule'):
        db.session.add(AppSetting(key='active_schedule', value='regular'))

    # Ramadan defaults: Mon–Sat 9:00–15:00, Sunday closed
    for day in range(7):
        is_sunday = (day == 6)
        for stype in ('regular', 'ramadan'):
            if not BusinessHours.query.filter_by(day_of_week=day, schedule_type=stype).first():
                close = _time(15, 0) if stype == 'ramadan' else _time(18, 0)
                db.session.add(BusinessHours(
                    day_of_week=day,
                    schedule_type=stype,
                    is_closed=is_sunday,
                    open_time=None if is_sunday else _time(9, 0),
                    close_time=None if is_sunday else close,
                ))
    db.session.commit()


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

    # Schema migrations + table creation + row seeding
    with app.app_context():
        _alter_tables()     # raw SQL: add missing columns before ORM is used
        db.create_all()     # create any brand-new tables (e.g. AppSetting)
        _seed_schedule_rows()  # ensure 14 hour rows + active_schedule setting

    return app
