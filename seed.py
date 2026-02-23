"""
Seed initial data into the database.
Run once after first deploy (or to reset to car-shop defaults):
    docker compose exec web python seed.py
"""
from datetime import time

from app import create_app
from app.models import db, User, Service, Staff, BusinessHours, Booking, AppSetting


def seed():
    app = create_app()
    with app.app_context():
        # ── Admin user ────────────────────────────────────────────────────────
        if not User.query.filter_by(email='admin@shop.com').first():
            admin = User(name='Admin', email='admin@shop.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            print('Created admin user: admin@shop.com / admin123')

        # ── Reset services, staff, and bookings ───────────────────────────────
        # Delete in FK-safe order: bookings → staff → services
        deleted_bookings = Booking.query.delete()
        deleted_staff    = Staff.query.delete()
        deleted_services = Service.query.delete()
        db.session.flush()
        print(f'Cleared {deleted_bookings} booking(s), {deleted_staff} staff, {deleted_services} service(s)')

        # ── Services ──────────────────────────────────────────────────────────
        services_data = [
            ('Oil Change',              'Full synthetic oil change with filter replacement.',          30,  45.00),
            ('Tire Rotation & Balance', 'Rotate and balance all four tires.',                         30,  30.00),
            ('Brake Inspection',        'Inspect and service brake pads, rotors, and fluid.',         60,  80.00),
            ('Full Detail & Wash',      'Interior and exterior deep clean and polish.',               90, 120.00),
            ('Engine Diagnostics',      'Computer scan and full engine health check.',                45,  60.00),
            ('AC Service & Recharge',   'Recharge refrigerant and inspect AC system components.',    60,  95.00),
            ('Battery Test & Replace',  'Test battery health and replace if needed.',                20,  35.00),
        ]
        for name, desc, duration, price in services_data:
            db.session.add(Service(name=name, description=desc, duration_minutes=duration, price=price))
            print(f'Created service: {name}')

        # ── Staff ─────────────────────────────────────────────────────────────
        staff_data = [
            ('Mike Torres',   'mike@autobook.com',  'Engine & Diagnostics'),
            ('Sara Al-Rashid','sara@autobook.com',  'Brakes & Tires'),
            ('James Kowalski','james@autobook.com', 'Detailing & AC'),
        ]
        for name, email, specialty in staff_data:
            db.session.add(Staff(name=name, email=email, specialty=specialty))
            print(f'Created staff: {name}')

        # ── Business hours ────────────────────────────────────────────────────
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        schedules = {
            'regular': [
                (0, time(8, 0), time(18, 0), False),
                (1, time(8, 0), time(18, 0), False),
                (2, time(8, 0), time(18, 0), False),
                (3, time(8, 0), time(18, 0), False),
                (4, time(8, 0), time(18, 0), False),
                (5, time(9, 0), time(17, 0), False),
                (6, None,       None,        True),   # Sunday closed
            ],
            'ramadan': [
                (0, time(9, 0), time(15, 0), False),
                (1, time(9, 0), time(15, 0), False),
                (2, time(9, 0), time(15, 0), False),
                (3, time(9, 0), time(15, 0), False),
                (4, time(9, 0), time(15, 0), False),
                (5, time(9, 0), time(13, 0), False),
                (6, None,       None,        True),   # Sunday closed
            ],
        }
        for stype, hours_data in schedules.items():
            for day, open_t, close_t, closed in hours_data:
                bh = BusinessHours.query.filter_by(day_of_week=day, schedule_type=stype).first()
                if bh is None:
                    bh = BusinessHours(day_of_week=day, schedule_type=stype)
                    db.session.add(bh)
                bh.is_closed  = closed
                bh.open_time  = open_t
                bh.close_time = close_t
                status = 'Closed' if closed else f'{open_t} – {close_t}'
                print(f'Set {stype} hours: {day_names[day]} {status}')

        # ── Active schedule default ───────────────────────────────────────────
        if not AppSetting.query.get('active_schedule'):
            db.session.add(AppSetting(key='active_schedule', value='regular'))
            print('Created setting: active_schedule = regular')

        db.session.commit()
        print('\nSeed complete.')


if __name__ == '__main__':
    seed()
