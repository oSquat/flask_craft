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
    
