
from flask import render_template

from . import logger
from . import main


@main.route('/', methods=['GET'])
def root():
    return render_template('root.html')

