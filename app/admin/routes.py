from datetime import datetime, time

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps

from . import bp
from ..models import db, User, Service, Staff, BusinessHours, Booking, AppSetting


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated


# ── Dashboard ────────────────────────────────────────────────────────────────

@bp.route('/')
@admin_required
def dashboard():
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)

    today_bookings = Booking.query.filter(
        Booking.start_time >= today_start,
        Booking.start_time <= today_end,
    ).order_by(Booking.start_time).all()

    total_bookings = Booking.query.count()
    pending_count = Booking.query.filter_by(status=Booking.STATUS_PENDING).count()
    confirmed_count = Booking.query.filter_by(status=Booking.STATUS_CONFIRMED).count()

    return render_template(
        'admin/dashboard.html',
        today_bookings=today_bookings,
        total_bookings=total_bookings,
        pending_count=pending_count,
        confirmed_count=confirmed_count,
        today=today,
    )


# ── Bookings ─────────────────────────────────────────────────────────────────

@bp.route('/bookings')
@admin_required
def bookings():
    query = Booking.query

    filter_date = request.args.get('date', '')
    filter_staff = request.args.get('staff_id', type=int)
    filter_status = request.args.get('status', '')

    if filter_date:
        try:
            d = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter(
                Booking.start_time >= datetime.combine(d, time.min),
                Booking.start_time <= datetime.combine(d, time.max),
            )
        except ValueError:
            pass

    if filter_staff:
        query = query.filter_by(staff_id=filter_staff)

    if filter_status:
        query = query.filter_by(status=filter_status)

    bookings = query.order_by(Booking.start_time.desc()).all()
    staff_list = Staff.query.all()

    return render_template(
        'admin/bookings.html',
        bookings=bookings,
        staff_list=staff_list,
        filter_date=filter_date,
        filter_staff=filter_staff,
        filter_status=filter_status,
    )


@bp.route('/bookings/<int:booking_id>/status', methods=['POST'])
@admin_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status', '')
    valid = [Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED, Booking.STATUS_CANCELLED]
    if new_status in valid:
        booking.status = new_status
        db.session.commit()
        flash('Booking #{} status updated to {}.'.format(booking_id, new_status), 'success')
    else:
        flash('Invalid status.', 'danger')
    return redirect(url_for('admin.bookings'))


# ── Services ──────────────────────────────────────────────────────────────────

@bp.route('/services', methods=['GET', 'POST'])
@admin_required
def services():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            duration = request.form.get('duration_minutes', type=int)
            price = request.form.get('price', type=float)

            if not name or not duration or price is None:
                flash('Name, duration, and price are required.', 'danger')
                form_data = {'name': name, 'description': description,
                             'duration_minutes': request.form.get('duration_minutes', ''),
                             'price': request.form.get('price', '')}
                return render_template('admin/services.html', services=Service.query.all(), form_data=form_data)
            else:
                service = Service(name=name, description=description, duration_minutes=duration, price=price)
                db.session.add(service)
                db.session.commit()
                flash('Service "{}" added.'.format(name), 'success')

        elif action == 'delete':
            service_id = request.form.get('service_id', type=int)
            service = Service.query.get_or_404(service_id)
            db.session.delete(service)
            db.session.commit()
            flash('Service deleted.', 'info')

        elif action == 'edit':
            service_id = request.form.get('service_id', type=int)
            service = Service.query.get_or_404(service_id)
            service.name = request.form.get('name', service.name).strip()
            service.description = request.form.get('description', service.description).strip()
            service.duration_minutes = request.form.get('duration_minutes', service.duration_minutes, type=int)
            service.price = request.form.get('price', service.price, type=float)
            db.session.commit()
            flash('Service updated.', 'success')

        return redirect(url_for('admin.services'))

    all_services = Service.query.all()
    return render_template('admin/services.html', services=all_services)


# ── Staff ─────────────────────────────────────────────────────────────────────

@bp.route('/staff', methods=['GET', 'POST'])
@admin_required
def staff():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            specialty = request.form.get('specialty', '').strip()

            if not name or not email:
                flash('Name and email are required.', 'danger')
                form_data = {'name': name, 'email': email, 'specialty': specialty}
                return render_template('admin/staff.html', staff_list=Staff.query.all(), form_data=form_data)
            elif Staff.query.filter_by(email=email).first():
                flash('A staff member with that email already exists.', 'danger')
                form_data = {'name': name, 'email': email, 'specialty': specialty}
                return render_template('admin/staff.html', staff_list=Staff.query.all(), form_data=form_data)
            else:
                member = Staff(name=name, email=email, specialty=specialty)
                db.session.add(member)
                db.session.commit()
                flash('Staff member "{}" added.'.format(name), 'success')

        elif action == 'delete':
            staff_id = request.form.get('staff_id', type=int)
            member = Staff.query.get_or_404(staff_id)
            db.session.delete(member)
            db.session.commit()
            flash('Staff member deleted.', 'info')

        elif action == 'edit':
            staff_id = request.form.get('staff_id', type=int)
            member = Staff.query.get_or_404(staff_id)
            member.name = request.form.get('name', member.name).strip()
            member.email = request.form.get('email', member.email).strip().lower()
            member.specialty = request.form.get('specialty', member.specialty).strip()
            db.session.commit()
            flash('Staff member updated.', 'success')

        return redirect(url_for('admin.staff'))

    all_staff = Staff.query.all()
    return render_template('admin/staff.html', staff_list=all_staff)


# ── Business Hours ────────────────────────────────────────────────────────────

@bp.route('/hours', methods=['GET', 'POST'])
@admin_required
def hours():
    DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    if request.method == 'POST':
        schedule_type = request.form.get('schedule_type', 'regular')
        if schedule_type not in ('regular', 'ramadan'):
            schedule_type = 'regular'

        for day in range(7):
            bh = BusinessHours.query.filter_by(day_of_week=day, schedule_type=schedule_type).first()
            if bh is None:
                bh = BusinessHours(day_of_week=day, schedule_type=schedule_type)
                db.session.add(bh)

            is_closed = bool(request.form.get(f'closed_{day}'))
            bh.is_closed = is_closed

            if not is_closed:
                open_str = request.form.get(f'open_{day}', '09:00')
                close_str = request.form.get(f'close_{day}', '18:00')
                try:
                    bh.open_time = datetime.strptime(open_str, '%H:%M').time()
                    bh.close_time = datetime.strptime(close_str, '%H:%M').time()
                except ValueError:
                    flash(f'Invalid time for {DAY_NAMES[day]}.', 'danger')

        db.session.commit()
        flash('Business hours updated.', 'success')
        return redirect(url_for('admin.hours', tab=schedule_type))

    active_schedule = AppSetting.get('active_schedule', 'regular')
    active_tab = request.args.get('tab', 'regular')
    if active_tab not in ('regular', 'ramadan'):
        active_tab = 'regular'

    regular_map = {bh.day_of_week: bh for bh in BusinessHours.query.filter_by(schedule_type='regular').all()}
    ramadan_map = {bh.day_of_week: bh for bh in BusinessHours.query.filter_by(schedule_type='ramadan').all()}

    return render_template(
        'admin/hours.html',
        regular_list=[regular_map.get(d) for d in range(7)],
        ramadan_list=[ramadan_map.get(d) for d in range(7)],
        active_schedule=active_schedule,
        active_tab=active_tab,
    )


# ── Calendar ──────────────────────────────────────────────────────────────────

@bp.route('/calendar')
@admin_required
def calendar():
    return render_template('admin/calendar.html')


@bp.route('/calendar/events')
@admin_required
def calendar_events():
    start_str = request.args.get('start', '')
    end_str   = request.args.get('end', '')

    query = Booking.query
    if start_str and end_str:
        try:
            start_dt = datetime.fromisoformat(start_str[:19])
            end_dt   = datetime.fromisoformat(end_str[:19])
            query = query.filter(Booking.start_time >= start_dt,
                                 Booking.start_time <= end_dt)
        except ValueError:
            pass

    colors = {
        Booking.STATUS_PENDING:   '#ffc107',
        Booking.STATUS_CONFIRMED: '#198754',
        Booking.STATUS_CANCELLED: '#dc3545',
    }
    events = []
    for b in query.all():
        events.append({
            'id':    b.id,
            'title': f'{b.service.name} · {b.user.name}',
            'start': b.start_time.isoformat(),
            'end':   b.end_time.isoformat(),
            'color': colors.get(b.status, '#6c757d'),
            'extendedProps': {
                'status':   b.status,
                'customer': b.user.name,
                'service':  b.service.name,
                'staff':    b.staff.name,
                'notes':    b.notes or '',
            },
        })
    return jsonify(events)


@bp.route('/hours/set-active', methods=['POST'])
@admin_required
def set_active_schedule():
    schedule = request.form.get('schedule', 'regular')
    if schedule in ('regular', 'ramadan'):
        AppSetting.set('active_schedule', schedule)
        flash('Active schedule switched.', 'success')
    return redirect(url_for('admin.hours', tab=schedule))
