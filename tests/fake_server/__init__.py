#!/usr/bin/env python
"""A fake Minecraft RCON server"""

import asyncio
from asyncio.exceptions import CancelledError
import logging 
import time

from rcon_server.rcon_server import RCONServer, logger
from rcon_server.rcon_message import RCONMessage

class DummyServer:
    """A dummy server until the asyncio server is created"""
    def is_serving(self):
        return False


class FakeServer(RCONServer):
    """A mock minecraft server accessible via rcon.

    Mimick's a minecraft server's properties, players, commands, etc..
    The object offers methods to manipulate server properties.
    """

    def __init__(self, bind=('localhost',25575), password=None):
        """Overload RCONServer's init

        Better defaults & internal setup to mimick a server.
        """
        self._world = 'My World'

        self.p = 0
        
        super().__init__(bind, password)

        self.command = {
            'list': self._list,
            'stop': self._stop,
        }

        self.server = DummyServer()

    async def listen(self):
        """Override parent method to make server is a class attribute."""

        self._loop = asyncio.get_event_loop()
        self.server = await self._loop.create_server(self.connection_factory,
                                          self.bind[0], self.bind[1])
        print(self.server)
        async with self.server:
            logger.info("starting server")
            for socket in self.server.sockets:
                # [:2] needed to remove the additional fields of INET6 sockets
                logger.info("listening on %s:%s" % socket.getsockname()[:2])
            try:
                await self.server.serve_forever()
            except CancelledError:
                pass

    def handle_execcommand(self, packet, connection):
        """Rcon server command handler."""
        command = packet.body.strip('/')
        logger.info(f'> {command}')
        id_ = packet.id + 1
        # type SERVERDATA_RESPONSE_VALUE
        type_ = 0
        handler = self.command.get(
                command, 
                self._bad_command_or_file_name
        )
        response = handler()
        logger.info(response)
        message = RCONMessage(
            id=id_,
            type=type_,
            body=response
        )
        connection.send_packet(message)

        if command == 'stop':
            self._exit()

    def _list(self):
        s = f'there are {self.p} players online'
        self.p += 1
        return s

    def _stop(self):
        s = (
            f'Stopping the server'
            f'\nStopping server'
            f'\nSaving players'
            f'\nSaving worlds'
            f'\nSaving chunks for level {self._world}/minecraft:overworld'
            f'\nSaving chunks for level {self._world}/minecraft:the_nether'
            f'\nSaving chunks for level {self._world}/minecraft:the_end'
            f'\nThreadedAnvilChunkStorage (world): All chunks are saved'
            f'\nThreadedAnvilChunkStorage (DIM-1): All chunks are saved'
            f'\nThreadedAnvilChunkStorage (DIM1): All chunks are saved'
            f'\nThreadedAnvilChunkStorage: All dimensions are saved'
            f'\nThread RCON Listener stopped'
        )
        return s

    def _bad_command_or_file_name(self):
        # this is incomplete, real server points to unknown command or argument
        s = (
            'Unknown or incomplete command, see below for error\n'
            '????<--[HERE]'
        )
        return s

    def _exit(self):
        """Exit the server"""
        if self.server.is_serving():
            self.server.close()
        while self.server.is_serving():
            time.sleep(0.25)

    @classmethod
    def generator(cls):
        logging.getLogger().addHandler(logging.StreamHandler())
        fake_server = cls(password='x')
        return fake_server


if __name__ == '__main__':
    logging.getLogger().addHandler(logging.StreamHandler())
    rcon = FakeServer(password='password')
    asyncio.run(rcon.listen())

# Example clients using mcrcon (pip install mcrcon):
# PYTHON
#
# >>> from mcrcon import MCRcon
#
# >>> with MCRCon('localhost', 'password') as mcr:
# ...   mcr.command('arbitrary command')
# 'arbitrary response'
# >>>
#

# COMMAND LINE
# $ mcrcon localhost
# Password: *******
# > help
# arbitrary response
#
