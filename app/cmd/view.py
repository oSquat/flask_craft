
import json
import re

from flask import current_app, request

from . import logger
from . import cmd

list_player_count = re.compile('(?<=There are )\\d*')
list_player_max = re.compile('(?<=a max of )\\d*')
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
    return ({'count': player_count,
        'max': player_max,
        'players': player_list.split(', ')
    }, 200)

@cmd.route('/kick/', methods=['GET', 'POST'])
def kick():
    player = request.json['player']
    logger.info(f'requested kick player {player}') 
    response = current_app.mcr.command(f'kick {player}')

    if response == 'No player was found':
        result = 'failure'
    else:
        result = 'success'
    json = {
        'result': result,
        'response': response
    }
    return (json, 200)
