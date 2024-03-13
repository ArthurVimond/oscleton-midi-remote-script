import errno
import logging
import re
import socket
import traceback
from typing import Tuple, Callable

from .OscletonMixin import OscletonMixin
from .OSCConstants import OSC_LISTEN_PORT, OSC_RESPONSE_PORT
from .pythonosc.osc_bundle import OscBundle
from .pythonosc.osc_message import OscMessage, ParseError
from .pythonosc.osc_message_builder import OscMessageBuilder, BuildError


class OSCServer(OscletonMixin):

    @staticmethod
    def set_message(func):
        OSCServer.show_message = func

    def __init__(self,
                 oscleton,
                 local_addr: Tuple[str, int] = ('0.0.0.0', OSC_LISTEN_PORT),
                 remote_addr: Tuple[str, int] = ('127.0.0.1', OSC_RESPONSE_PORT)):
        """
        Class that handles OSC server responsibilities, including support for sending
        reply messages.

        Implemented because pythonosc's OSC server causes a beachball when handling
        incoming messages. To investigate, as it would be ultimately better not to have
        to roll our own.

        Args:
            local_addr: Local address and port to listen on.
                        By default, binds to the wildcard address 0.0.0.0, which means listening on
                        every available local IPv4 interface (including 127.0.0.1).
            remote_addr: Remote address to send replies to, by default. Can be overridden in send().
        """

        self._oscleton = oscleton
        self._local_addr = local_addr
        self._remote_addr = remote_addr
        self._response_port = remote_addr[1]

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)
        self._socket.bind(self._local_addr)
        self._callbacks = {}

        self.logger = logging.getLogger("oscleton")
        self.logger.info("Starting OSC server (local %s, response port %d)",
                         str(self._local_addr), self._response_port)

        self.add_handler('/live/set_peer', self._set_peer)
        self.add_handler('/live/config/discover_ip', self._discover_ip)

    def set_peer(self, host):
        (_, current_port) = self._remote_addr
        self.log_message('Oscleton: reconfigured to send to ' + host + ':' + str(current_port))
        self._remote_addr = (host, current_port)

    def _set_peer(self, msg):
        host = msg[1]
        port = msg[2]
        self.log_message('Oscleton: reconfigured to send to ' + host + ':' + str(port))
        self._remote_addr = (host, port)
        self.send('/live/set_peer/success', (True,))
        self._oscleton.set_linked_device_ip(host)

    def _discover_ip(self, msg):
        host = msg[1]
        port = msg[2]

        # Send back the computer IP
        computer_ip = str(msg[3])

        self.log_message('Oscleton: IP discovered with success for ' + host + ':' + str(port))
        self._remote_addr = (host, port)
        self.send('/live/config/discover_ip/success', (computer_ip,))
        self._oscleton.set_linked_device_ip(host)

    def add_handler(self, address: str, handler: Callable) -> None:
        """
        Add an OSC handler.

        Args:
            address: The OSC address string
            handler: A handler function, with signature:
                     params: Tuple[Any, ...]
        """
        self._callbacks[address] = handler

    def clear_handlers(self) -> None:
        """
        Remove all existing OSC handlers.
        """
        self._callbacks = {}

    def send(self,
             address: str,
             params: Tuple = (),
             remote_addr: Tuple[str, int] = None) -> None:
        """
        Send an OSC message.

        Args:
            address: The OSC address (e.g. /frequency)
            params: A tuple of zero or more OSC params
            remote_addr: The remote address to send to, as a 2-tuple (hostname, port).
                         If None, uses the default remote address.
        """
        msg_builder = OscMessageBuilder(address)
        for param in params:
            msg_builder.add_arg(param)

        try:
            msg = msg_builder.build()
            if remote_addr is None:
                remote_addr = self._remote_addr
            self._socket.sendto(msg.dgram, remote_addr)
        except BuildError:
            self.logger.error("OSCServer: OSC build error: %s" % (traceback.format_exc()))

    def process_message(self, message, remote_addr):
        if message.address in self._callbacks:
            callback = self._callbacks[message.address]
            params = [message.address] + message.params
            rv = callback(params)

            if rv is not None:
                assert isinstance(rv, tuple)
                remote_hostname, _ = remote_addr
                response_addr = (remote_hostname, self._response_port)
                self.send(address=message.address,
                          params=rv,
                          remote_addr=response_addr)
        elif "*" in message.address:
            regex = message.address.replace("*", "[^/]+")
            for callback_address, callback in self._callbacks.items():
                if re.match(regex, callback_address):
                    try:
                        rv = callback(message.params)
                    except ValueError:
                        # --------------------------------------------------------------------------------
                        # Don't throw errors for queries that require more arguments
                        # (e.g. /live/track/get/send with no args)
                        # --------------------------------------------------------------------------------
                        continue
                    except AttributeError:
                        # --------------------------------------------------------------------------------
                        # Don't throw errors when trying to create listeners for properties that can't
                        # be listened for (e.g. can_be_armed, is_foldable)
                        # --------------------------------------------------------------------------------
                        continue
                    if rv is not None:
                        assert isinstance(rv, tuple)
                        remote_hostname, _ = remote_addr
                        response_addr = (remote_hostname, self._response_port)
                        self.send(address=callback_address,
                                  params=rv,
                                  remote_addr=response_addr)
        else:
            self.logger.error("OSCServer: Unknown OSC address: %s" % message.address)

    def process_bundle(self, bundle, remote_addr):
        for i in bundle:
            if OscBundle.dgram_is_bundle(i.dgram):
                self.process_bundle(i, remote_addr)
            else:
                self.process_message(i, remote_addr)

    def parse_bundle(self, data, remote_addr):
        bundle = OscBundle(data)
        if bundle.num_contents == 0:
            try:
                message = OscMessage(data)
                self.process_message(message, remote_addr)
            except ParseError:
                self.logger.error("OSCServer: OSC parse error: %s" % (traceback.format_exc()))
        else:
            self.process_bundle(bundle, remote_addr)

    def process(self) -> None:
        """
        Synchronously process all data queued on the OSC socket.
        """
        try:
            repeats = 0
            while True:
                # --------------------------------------------------------------------------------
                # Loop until no more data is available.
                # --------------------------------------------------------------------------------
                data, remote_addr = self._socket.recvfrom(65536)
                # --------------------------------------------------------------------------------
                # Update the default reply address to the most recent client. Used when
                # sending (e.g) /live/song/beat messages and listen updates.
                #
                # This is slightly ugly and prevents registering listeners from different IPs.
                # --------------------------------------------------------------------------------
                self._remote_addr = (remote_addr[0], OSC_RESPONSE_PORT)
                self.parse_bundle(data, remote_addr)

        except socket.error as e:
            if e.errno == errno.ECONNRESET:
                # --------------------------------------------------------------------------------
                # This benign error seems to occur on startup on Windows
                # --------------------------------------------------------------------------------
                self.logger.warning("OSCServer: Non-fatal socket error: %s" % (traceback.format_exc()))
            elif e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                # --------------------------------------------------------------------------------
                # Another benign networking error, throw when no data is received
                # on a call to recvfrom() on a non-blocking socket
                # --------------------------------------------------------------------------------
                pass
            else:
                # --------------------------------------------------------------------------------
                # Something more serious has happened
                # --------------------------------------------------------------------------------
                self.logger.error("OSCServer: Socket error: %s" % (traceback.format_exc()))

        except Exception as e:
            self.logger.error("OSCServer: Error handling OSC message: %s" % e)
            self.logger.warning("OSCServer: %s" % traceback.format_exc())

    def shutdown(self) -> None:
        """
        Shutdown the server network sockets.
        """
        self._socket.close()
