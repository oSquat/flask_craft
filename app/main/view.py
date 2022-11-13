
from . import logger
from . import main

@main.route('/', methods=['GET'])
def root():
    return ('hello minecraft', 200)
