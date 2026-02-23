from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from . import bp
from ..models import db, User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash('Welcome back, {}!'.format(user.name), 'success')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html', form_data={'email': email, 'remember': remember})

    return render_template('auth/login.html')


@bp.route('/register')
def register():
    flash('Registration is not available. Please contact an administrator.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        new = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')

        if not current_user.check_password(current):
            flash('Current password is incorrect.', 'danger')
        elif len(new) < 6:
            flash('New password must be at least 6 characters.', 'danger')
        elif new != confirm:
            flash('New passwords do not match.', 'danger')
        else:
            current_user.set_password(new)
            db.session.commit()
            flash('Password updated successfully.', 'success')
            return redirect(url_for('main.index'))

    return render_template('auth/change_password.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
