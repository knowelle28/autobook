from flask import render_template, redirect, request, session, url_for

from . import bp
from ..models import Service


@bp.route('/set-lang/<lang>')
def set_lang(lang):
    if lang in ('en', 'ar'):
        session['lang'] = lang
    return redirect(request.referrer or url_for('main.index'))


@bp.route('/')
def index():
    services = Service.query.all()
    return render_template('main/index.html', services=services)


@bp.route('/services')
def services():
    services = Service.query.all()
    return render_template('main/services.html', services=services)
