import logging

from flask import Blueprint

main = Blueprint('main', __name__, template_folder='templates')
logger = logging.getLogger('main')

from . import view
