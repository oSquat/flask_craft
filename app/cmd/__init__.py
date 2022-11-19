import logging

from flask import Blueprint

cmd = Blueprint('cmd', __name__)
logger = logging.getLogger('cmd')

from . import view
