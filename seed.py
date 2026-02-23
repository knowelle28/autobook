"""
Seed initial data into the database.
Run once after first deploy:
    docker compose exec web python seed.py
"""
from datetime import time

from app import create_app
from app.models import db, User, Service, Staff, BusinessHours, AppSetting


def seed():
    app = create_app()
    with app.app_context():
        # ── Admin user ────────────────────────────────────────────────────────
        if not User.query.filter_by(email='admin@shop.com').first():
            admin = User(name='Admin', email='admin@shop.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            print('Created admin user: admin@shop.com / admin123')

        # ── Services ──────────────────────────────────────────────────────────
        services_data = [
            ('Haircut',          'Classic cut & style for all hair types.',         30,  25.00),
            ('Beard Trim',       'Shape and define your beard.',                    20,  15.00),
            ('Color Treatment',  'Full color, highlights, or balayage.',            90,  85.00),
            ('Facial',           'Deep cleansing and rejuvenating facial.',         60,  55.00),
            ('Swedish Massage',  'Relaxing full-body massage.',                     60,  70.00),
        ]
        for name, desc, duration, price in services_data:
            if not Service.query.filter_by(name=name).first():
                db.session.add(Service(name=name, description=desc, duration_minutes=duration, price=price))
                print(f'Created service: {name}')

        # ── Staff ─────────────────────────────────────────────────────────────
        staff_data = [
            ('Alice Johnson', 'alice@shop.com',   'Hair & Color'),
            ('Bob Martinez',  'bob@shop.com',     'Beard & Grooming'),
            ('Carol Chen',    'carol@shop.com',   'Skincare & Massage'),
        ]
        for name, email, specialty in staff_data:
            if not Staff.query.filter_by(email=email).first():
                db.session.add(Staff(name=name, email=email, specialty=specialty))
                print(f'Created staff: {name}')

        # ── Business hours ────────────────────────────────────────────────────
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        schedules = {
            'regular': [
                (0, time(9, 0), time(18, 0), False),
                (1, time(9, 0), time(18, 0), False),
                (2, time(9, 0), time(18, 0), False),
                (3, time(9, 0), time(18, 0), False),
                (4, time(9, 0), time(18, 0), False),
                (5, time(9, 0), time(18, 0), False),
                (6, None,       None,        True),   # Sunday closed
            ],
            'ramadan': [
                (0, time(9, 0), time(15, 0), False),
                (1, time(9, 0), time(15, 0), False),
                (2, time(9, 0), time(15, 0), False),
                (3, time(9, 0), time(15, 0), False),
                (4, time(9, 0), time(15, 0), False),
                (5, time(9, 0), time(15, 0), False),
                (6, None,       None,        True),   # Sunday closed
            ],
        }
        for stype, hours_data in schedules.items():
            for day, open_t, close_t, closed in hours_data:
                if not BusinessHours.query.filter_by(day_of_week=day, schedule_type=stype).first():
                    db.session.add(BusinessHours(
                        day_of_week=day,
                        schedule_type=stype,
                        open_time=open_t,
                        close_time=close_t,
                        is_closed=closed,
                    ))
                    status = 'Closed' if closed else f'{open_t} – {close_t}'
                    print(f'Created {stype} hours: {day_names[day]} {status}')

        # ── Active schedule default ───────────────────────────────────────────
        if not AppSetting.query.get('active_schedule'):
            db.session.add(AppSetting(key='active_schedule', value='regular'))
            print('Created setting: active_schedule = regular')

        db.session.commit()
        print('\nSeed complete.')


if __name__ == '__main__':
    seed()
