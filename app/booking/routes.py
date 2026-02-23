from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from . import bp
from ..models import db, Service, Staff, BusinessHours, Booking


@bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    services = Service.query.all()
    staff_list = Staff.query.all()

    if request.method == 'POST':
        service_id = request.form.get('service_id', type=int)
        staff_id = request.form.get('staff_id', type=int)
        start_str = request.form.get('start_time', '')
        notes = request.form.get('notes', '').strip()

        def _rerender(msg):
            flash(msg, 'danger')
            form_data = {'service_id': service_id, 'staff_id': staff_id,
                         'start_time': start_str, 'notes': notes}
            return render_template('booking/book.html', services=services,
                                   staff_list=staff_list, form_data=form_data)

        service = Service.query.get(service_id)
        staff = Staff.query.get(staff_id)

        # Basic presence checks
        if not service or not staff:
            return _rerender('Please select a valid service and staff member.')

        # Parse datetime
        try:
            start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            return _rerender('Invalid date/time format.')

        end_time = start_time + timedelta(minutes=service.duration_minutes)

        # 1. Must be in the future
        if start_time <= datetime.utcnow():
            return _rerender('Booking must be scheduled in the future.')

        # 2. Check business hours
        day_of_week = start_time.weekday()  # 0=Mon, 6=Sun
        bh = BusinessHours.query.filter_by(day_of_week=day_of_week).first()
        if bh is None or bh.is_closed:
            return _rerender('We are closed on that day.')

        if start_time.time() < bh.open_time or end_time.time() > bh.close_time:
            return _rerender(
                'Booking must be within business hours ({} – {}).'.format(
                    bh.open_time.strftime('%H:%M'), bh.close_time.strftime('%H:%M')
                )
            )

        # 3. Check staff overlap
        conflict = Booking.query.filter(
            Booking.staff_id == staff_id,
            Booking.status != Booking.STATUS_CANCELLED,
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        ).first()

        if conflict:
            return _rerender(
                '{} is not available at that time. Please choose a different time or staff member.'.format(
                    staff.name
                )
            )

        # All checks passed — create booking
        booking = Booking(
            user_id=current_user.id,
            service_id=service_id,
            staff_id=staff_id,
            start_time=start_time,
            end_time=end_time,
            status=Booking.STATUS_PENDING,
            notes=notes,
        )
        db.session.add(booking)
        db.session.commit()

        flash('Booking confirmed for {} on {}!'.format(service.name, start_time.strftime('%b %d at %H:%M')), 'success')
        return redirect(url_for('booking.my_bookings'))

    return render_template('booking/book.html', services=services, staff_list=staff_list)


@bp.route('/my-bookings')
@login_required
def my_bookings():
    bookings = (
        Booking.query
        .filter_by(user_id=current_user.id)
        .order_by(Booking.start_time.desc())
        .all()
    )
    return render_template('booking/my_bookings.html', bookings=bookings, now=datetime.utcnow())


@bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        flash('You cannot cancel this booking.', 'danger')
        return redirect(url_for('booking.my_bookings'))

    if booking.status == Booking.STATUS_CANCELLED:
        flash('This booking is already cancelled.', 'warning')
        return redirect(url_for('booking.my_bookings'))

    if booking.start_time <= datetime.utcnow():
        flash('You cannot cancel a past booking.', 'warning')
        return redirect(url_for('booking.my_bookings'))

    booking.status = Booking.STATUS_CANCELLED
    db.session.commit()
    flash('Your booking has been cancelled.', 'info')
    return redirect(url_for('booking.my_bookings'))
