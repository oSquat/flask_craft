import logging

from flask import Blueprint

main = Blueprint('main', __name__)
logger = logging.getLogger('main')

from . import view
