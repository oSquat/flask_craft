
import asyncio
import threading
import logging
import os
import subprocess
import sys
import time

from mcrcon import MCRcon
import pytest

from fake_server import FakeServer


class SysExitThread(threading.Thread):
    """Pass exception from thread run to the parent"""

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self._exc = None

    def run(self):
        try:
            super().run()
        except SystemExit as exc:
            self._exc = exc

    def join(self, timeout=None):
        super().join(timeout=timeout)
        if self._exc:
            raise self._exc

def pytest_configure(config):
    """Define markers to categorize tests.

    Run a specific category using pytest with the -m argument.
    """
    pass

def pytest_addoption(parser):
    """Add arbitrary arguments to pytest."""
    parser.addoption('--realserver', action='store_true', dest='realserver',
            default=False, help='only run tests against the real server')

@pytest.fixture(scope='session')
def app(tmux_session):
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

@pytest.fixture(scope='function')
def fake_server():
    """Yield a fake minecraft server available via rcon"""
    logging.getLogger().addHandler(logging.StreamHandler())
    fake_server = FakeServer(password='password')

    def _run():
        asyncio.run(fake_server.listen())

    t = SysExitThread(target=_run)
    t.start()
    # it takes a moment for our server to start, but is there a better way to
    #   test for this? I would expect fake_server.server.is_serving() to work.
    while not fake_server.server.is_serving():
        time.sleep(0.25)
    yield fake_server

@pytest.fixture(scope='function')
def mcr(fake_server):
    """Yield an active rcon connection to the fake server"""
    with MCRcon('localhost', 'password') as mcr:
        yield mcr
        if fake_server.server.is_serving():
            mcr.command('stop')        
