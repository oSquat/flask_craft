
import json
import re

from flask import current_app

from . import logger
from . import cmd

list_player_count = re.compile('(?<=There are )\d*')
list_player_max = re.compile('(?<=a max of )\d*')
list_players = re.compile('(?<=online: ).*')

@cmd.route('/', methods=['GET'])
def root():
    return ('cmd', 200)

@cmd.route('/list/')
def list():
    response = current_app.mcr.command('list')
    match = list_player_count.findall(response)
    if not match:
        raise RuntimeError('missing or unexpected list result on count:')
    player_count = int(match[0])
    match = list_player_max.findall(response)
    if not match:
        raise RuntimeError('missing or unexpected list result on max')
    player_max = int(match[0])
    match = list_players.findall(response)
    if not match:
        raise RuntimeError('missing or unexpected list result on player list')
    player_list = match[0]
    d = {
            'count': player_count,
            'max': player_max,
            'players': player_list.split(', ')
        }
    return (d, 200)

@cmd.route('/kick/<user>', methods=['GET'])
def kick(user):
    current_app.tmux_pane.send_keys(f'/kick {user}')
    return (f'kicked {user}', 200)
