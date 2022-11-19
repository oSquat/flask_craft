
from flask import current_app

from . import logger
from . import cmd

@cmd.route('/', methods=['GET'])
def root():
    return ('cmd', 200)

@cmd.route('/kick/<user>', methods=['GET'])
def kick(user):
    current_app.tmux_pane.send_keys(f'/kick {user}')
    return (f'kicked {user}', 200)
