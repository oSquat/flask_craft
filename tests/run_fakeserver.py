#!/usr/bin/env python
#

import asyncio
import time

from fake_server import FakeServer, SysExitThread
from MCRconLib import MCRcon


if __name__ == '__main__':

    print('instantiating FakeServer as "fake_server"...')
    # TODO: This code is shared with conftest, can I make it a function?
    fake_server = FakeServer(password='password')

    def _run():
        asyncio.run(fake_server.listen())

    t = SysExitThread(target=_run)
    t.start()
    while not fake_server.server.is_serving():
        time.sleep(0.25)

    print('fake_server loaded...')

    print('instantiating MCRcon as "mcr"...')
    mcr = MCRcon('localhost', 'password')

    print('connecting mcr...')
    mcr.connect()

    print('mcr connected...')
    print('\n')
    print('To terminate the fake_server, then exit():')
    print('>>> mcr.command("stop")')
    print('')
    # TODO: Intercept sigint and handle server termination

