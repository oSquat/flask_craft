
from flask import render_template

from . import logger
from . import main


@main.route('/', methods=['GET'])
def root():
    return render_template('root.html')

@main.route('/player/')
@main.route('/player/<player>/', methods=['GET'])
def player(player):
   return render_template('player.html', player=player) 
