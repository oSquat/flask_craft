
import asyncio
import threading
import logging
import os
import subprocess
import sys
import struct
import select
import time

from mcrcon import MCRcon as MCRconLib
import pytest

from fake_server import FakeServer

sys.path.append(os.getcwd())
os.environ['FLASK_TESTING'] = '1'

from app import create_app, fake_app


class MCRcon(MCRconLib):
    """Override MCRcon to add a functioning id to rcon messaging.

    The MCRcon does not implement an ID in RCON messages, instead all
    message ID's are 0. I don't know if it's a bug with rcon-server or
    MCRcon, but communication between the two occasionally got out of
    sync. The client would send a request, the server would respond but
    then a blank message would be received by the client. This blank
    message would queue and all subsequent commands would get a response
    from the previous command.

      client            server
      ------            ------
      connect    -->    
                 <--    reply
      auth       -->    
                 <--    reply
                x<--    extrapacket            
      command_1  --> 
      <receive extra packet>
                x<--    reply_1
      command_2  -->    
      <receive reply_1>
                x<--    reply_2

    I logged every packet out of the server up to the transport and
    couldn't find any deviation between failure and success.
    """
    def __init__(self, host, password, port=25575, tlsmode=0, timeout=5):
        """Extends init to define self.id_"""
        super().__init__(host, password, port, tlsmode, timeout)
        self.id_ = 0

    def _send(self, out_type, out_data):
        """Override to discard resposne packets not matching the request ID."""
        if self.socket is None:
            raise MCRconException("Must connect before sending data")

        # Send a request packet
        out_id = self.id_
        out_payload = (
            struct.pack("<ii", out_id, out_type) + out_data.encode("utf8") + b"\x00\x00"
        )
        self.id_ += 1
        out_length = struct.pack("<i", len(out_payload))
        self.socket.send(out_length + out_payload)

        # Read response packets
        in_data = ""
        while True:
            # Read a packet
            (in_length,) = struct.unpack("<i", self._read(4))
            in_payload = self._read(in_length)
            in_id, in_type = struct.unpack("<ii", in_payload[:8])
            in_data_partial, in_padding = in_payload[8:-2], in_payload[-2:]

            # Sanity checks
            if in_padding != b"\x00\x00":
                raise MCRconException("Incorrect padding")
            if in_id == -1:
                raise MCRconException("Login failed")

            # Record the response
            in_data += in_data_partial.decode("utf8")

            # If there's nothing more to receive, return the response
            if len(select.select([self.socket], [], [], 0)[0]) == 0:
                # Discard packets if the id doesn't match our last request's ID
                if in_id != out_id:
                    in_data = ""
                    continue
                return in_data


class SysExitThread(threading.Thread):
    """Pass exception from thread run to the parent"""

    def __init__(self, group=None, target=None, 
                 name=None, args=(), kwargs=None, 
                 *, daemon=None):
        super().__init__(group=group, target=target, 
                         name=name, args=args, 
                         kwargs=kwargs, daemon=daemon)
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

@pytest.fixture(scope='function')
def fake_server():
    """Yield a fake minecraft server available via rcon"""
    #logging.getLogger().addHandler(logging.StreamHandler())
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

