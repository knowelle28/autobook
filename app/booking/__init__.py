from flask import Blueprint

bp = Blueprint('booking', __name__, url_prefix='/booking')

from . import routes  # noqa: F401, E402
