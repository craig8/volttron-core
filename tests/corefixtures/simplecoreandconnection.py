import logging

import gevent

from volttron.client.vip.agent import Agent
from volttron.client.vip.agent.core import Core
from volttron.decorators import connection_builder, core_builder
from volttron.types.auth.auth_credentials import Credentials
from volttron.types.bases import Connection, CoreLoop
from volttron.types.factories import ConnectionBuilder
from volttron.types.message import Message

_log = logging.getLogger(__name__)


class SimpleCoreBuilder:

    def __init__(self, builder: ConnectionBuilder) -> None:
        self._connection_builder: ConnectionBuilder = builder

    class SimplisticCore(Core):

        def __init__(self, owner, credentials: Credentials, connection_builder: ConnectionBuilder):
            super().__init__(owner, credentials, connection_builder)

        def loop(self, running_event):
            # pre-setup
            _log.debug("Pre-setup")
            yield    # done with presetup
            _log.debug("Connecting and starting main vip loop.")

            # Do the connection for this core class.
            self._connection.connect()

            if self._connection.connected:
                # This is what triggers the event to move to the next step
                running_event.set()

            def vip_loop():
                while True:
                    gevent.sleep(1)
                    _log.debug("Running vip loop")

            # Start the main vip loop, note this is defined right here so it has the state of the current object.
            yield gevent.spawn(vip_loop)

            _log.debug("Pre-stop")
            # pre-stop
            yield

            _log.debug("Finish and die")
            # finish
            yield

    def build(self, credentials: Credentials, owner: Agent = None) -> CoreLoop:
        return SimpleCoreBuilder.SimplisticCore(owner=owner,
                                                credentials=credentials,
                                                connection_builder=self._connection_builder)


class SimpleConnectionFactory:

    def __init__(self, address: str):
        self._address = address

    def address(self) -> str:
        return self._address

    class Conn(Connection):

        def __init__(self, address, credentials: Credentials):
            self._connected = False
            self._address = address
            self._credentials = credentials
            self._sent_messages: list[Message] = []

        @property
        def connected(self) -> bool:
            return self._connected

        def connect(self):
            self._connected = True

        def disconnect(self):
            self._connected = False

        def is_connected(self) -> bool:
            return self._connected

        def send_vip_message(self, message: Message):
            self._sent_messages.append(message)

        def recieve_vip_message(self) -> Message:
            pass

    def build(self, credentials: Credentials) -> Connection:
        return self.Conn(self._address, credentials=credentials)
