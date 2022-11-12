"""Test fake minecraft server commands behave as expected"""

import subprocess
import time

from mcrcon import MCRconException
import pytest

default = pytest.mark.skipif("config.getoption('realserver')")


@default
def test_stop(fake_server, mcr):
    """The server shuts down when issued the stop command"""
    assert fake_server.server.is_serving() == True
    response = mcr.command('stop')
    assert fake_server.server.is_serving() == False

def test_list_0(mcr):
    """Test /list responds with 0 players"""
    response = mcr.command('/list')
    while response == '':
        time.sleep(0.25)
        print('waiting on response')
    assert response.strip() == 'There are 0 of a max of 5 players online:' 

def test_list_player_count(fake_server, mcr):
    """Joining players increments the count in /list response"""
    c = 0x40
    for i in range(1,4):
        fake_server.player_join(chr(c+i))
        response = mcr.command('/list')
        assert response.strip().startswith(f'There are {i} of a max of 5 players online:')

def test_list_shows_player_names(fake_server, mcr):
    """Join players to the server and issue the /list command.

    Test the players are named in the output.
    """
    players = ['rusty_shackleford', 'mvp0849']
    for player in players:
        fake_server.player_join(player)
    response = mcr.command('/list')
    for player in players:
        assert player in response
    
