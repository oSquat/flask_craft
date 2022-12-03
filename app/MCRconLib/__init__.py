"""Modified implementation of MCRCon for testing/dev with fake_server"""

import select
import struct

from mcrcon import MCRcon as MCRconLib, MCRconException


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
