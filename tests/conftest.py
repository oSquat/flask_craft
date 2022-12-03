
import asyncio
import threading
import logging
import os
import random
import subprocess
import sys
import string
import time

import pytest

from fake_server import FakeServer, SysExitThread
from MCRconLib import MCRcon

sys.path.append(os.getcwd())
os.environ['FLASK_TESTING'] = '1'

from app import create_app, fake_app

def pytest_configure(config):
    """Define markers to categorize tests.

    Run a specific category using pytest with the -m argument.
    """
    pass

def pytest_addoption(parser):
    """Add arbitrary arguments to pytest."""
    parser.addoption('--realserver', action='store_true', dest='realserver',
            default=False, help='only run tests against the real server')

def get_random(n, chars='alnum'):
    """Get a random [alpha]numeric string with a length of n-characters.

    Arguments:
    n       - number of characters
    chars   - "alnum" or "num"
    """
    if chars=='num':
        return ''.join(random.choice(string.digits) for _ in range(n))
    elif chars=='alnum':
        return ''.join(random.choice(
                string.ascii_uppercase + string.digits) for _ in range(n))
    else:
        raise RuntimeError('chars must be either "alnum" or "num".')

@pytest.fixture(scope='function')
def fake_server():
    """Yield a fake minecraft server available via rcon"""
    fake_server = FakeServer(password='password')

    def _run():
        asyncio.run(fake_server.listen())

    t = SysExitThread(target=_run)
    t.start()
    # it takes a moment for our server to start
    while not fake_server.server.is_serving():
        time.sleep(0.25)
    yield fake_server
    try:
        if fake_server.server.is_serving():
            with MCRcon('localhost', 'password') as mcr:
                mcr.command('stop')        
    except ConnectionResetError:
        # I think sometimes fake_server serves for slightly longer than we
        # expect and a ConnectionResetError happens when we try to establish
        # an RCON connection. I think there a re a lot of these odd timing
        # issues that come up when using concurrency.
        pass

@pytest.fixture(scope='function')
def mcr(fake_server):
    """Yield an active rcon connection to the fake server"""
    with MCRcon('localhost', 'password') as mcr:
        yield mcr
        if fake_server.server.is_serving():
            mcr.command('stop')        

@pytest.fixture(scope='function')
def app():
    """Yield a fake flask app"""
    alias = os.path.basename(os.getcwd())
    flask_app = create_app(alias)
    app_context = flask_app.test_request_context()
    app_context.push()
    yield flask_app

@pytest.fixture(scope='function')
def client(app):
    """Yield a flask test client"""
    with app.test_client() as client:
        yield client

