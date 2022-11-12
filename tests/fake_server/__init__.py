#!/usr/bin/env python
"""A fake Minecraft RCON server"""

import asyncio
from asyncio.exceptions import CancelledError
import logging 
import time

from rcon_server.rcon_server import RCONServer, logger
from rcon_server.rcon_message import RCONMessage
from rcon_server.rcon_packet import RCONPacket


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
        self._max_players = 5
        self._players = list()
        
        super().__init__(bind, password)

        self.command = {
            'list': self._list,
            'stop': self._stop,
            'kick': self._kick,
        }

        self.server = DummyServer()

    @classmethod
    def generator(cls):
        logging.getLogger().addHandler(logging.StreamHandler())
        fake_server = cls(password='x')
        return fake_server

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
        command_line = packet.body.strip('/')
        argv = command_line.split(' ')
        command = argv[0]

        logger.info(f'> {command}')
        id_ = packet.id
        type_ = RCONPacket.SERVERDATA_RESPONSE_VALUE
        handler = self.command.get(
                command, 
                self._bad_command_or_file_name
        )
        response = handler(*argv[1:])
        logger.info(response)
        message = RCONMessage(
            id=id_,
            type=type_,
            body=response
        )
        connection.send_packet(message)

        if command == 'stop':
            self._exit()

    # -------------------------
    # Server management methods
    # -------------------------
    def player_join(self, name):
        """A player joins the server."""
        if name in self._players:
            raise RuntimeError(f'{name} already joined')
        self._players.append(name)
        # The following info is also logged, but I'm not ready to simulate it
        # f'{name}[/saddress:sport] logged in with entity id <UUID> at (X, Y, Z)
        logger.info(f'{name} joined the game')

    def player_leave(self, name):
        if not name in self._players:
            raise RuntimeError(f'invalid player {name}')
        self._players.remove(name)
        logger.info(f'{name} lost connection: Disconnected')
        logger.info(f'{name} left the game')

    # -------------------------
    # Minecraft server commands
    # -------------------------
    def _list(self):
        """Show a count of players in game and list them"""
        s = (
            f'There are {len(self._players)} of a max of {self._max_players} '
            'players online: '
            f"{''.join(self._players)}"
        )
        return s

    def _kick(self, name, reason='Kicked by an operator'):
        """Kick a user, optionally with a customized reason"""
        if not name in self._players:
            return 'No player was found'
        self._players.remove(name)
        logger.info(f'{name} lost connection: {reason}')
        logger.info(f'{name} left the game')
        return f'Kicked {name}: {reason}'

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
