from __future__ import annotations
from volttron.client.vip.agent import Agent, Core
#from volttron.decorators import core, agent_starter, factory
from volttron.decorators import core_builder, connection_builder, agent_starter
from volttron.server.containers import Frozen
from volttron.types.auth.auth_credentials import Credentials
from volttron.types.message import Message
from volttron.types.protocols import AgentStarter, ConnectionFactory, Connection, CoreLoop
from volttron.utils.context import EnvironmentalContext


@agent_starter
class AgentStarterInstance(AgentStarter):

    agents_started = Frozen()

    def __init__(self):
        self.agents_started = {}

    def start(self, agent: Agent):
        self.agents_started[agent.core.identity] = agent

    def stop(self, identity: str):
        if self.agents_started.get(identity):
            self.agents_started[identity].stop()
            del self.agents_started[identity]


@connection_builder
class ConnectionFactoryInstance:

    class Conn(Connection):

        def __init__(self, address, credentials: Credentials):
            self._connected = False
            self._address = address
            self._credentials = credentials

        def connect(self, address: str, credentials: Credentials):
            ...

        def disconnect(self):
            ...

        def is_connected(self) -> bool:
            return self._connected

        def send_vip_message(self, message: Message):
            ...

        def recieve_vip_message(self) -> Message:
            ...

    def build(self, credentials: Credentials) -> Connection:
        env = EnvironmentalContext.from_env()
        return self.Conn(address=env.address, credentials=credentials)


#factory(ConnectionFactoryInstance, ConnectionFactory)


@core_builder
class CoreInstanceBuilder:

    class CoreInstance(Core):

        def __init__(self, owner, credentials: Credentials, connection_factory: ConnectionFactory):
            super().__init__(owner=owner, credentials=credentials, connection_factory=connection_factory)
            ...

        def version(self) -> str:
            ...

        @property
        def connected(self) -> bool:
            ...

        def get_connected(self) -> bool:
            ...

        def set_connected(self, value: bool):
            ...

        def stop(self, timeout: int = None, platform_shutdown: bool = False):
            ...

        def register(self, name: str, handler: callable, error_handler: callable = None):
            ...

        def handle_error(self, message: str):
            ...

        def create_event_handlers(self, state: int, hello_response_event: callable,
                                  running_event: callable) -> tuple[callable, callable, callable]:
            ...

            def connection_failed_check():
                ...
                # If we don't have a verified connection after 10.0 seconds
                # shut down.
                # if hello_response_event.wait(10.0):
                #     return
                # _log.error("No response to hello message after 10 seconds.")
                # _log.error("Type of message bus used {}".format(self.messagebus))
                # _log.error("A common reason for this is a conflicting VIP IDENTITY.")
                # _log.error("Another common reason is not having an auth entry on"
                #            "the target instance.")
                # _log.error("Shutting down agent.")
                # _log.error("Possible conflicting identity is: {}".format(self.identity))

                # self.stop(timeout=10.0)

            def hello():
                ...
                # # Send hello message to VIP router to confirm connection with
                # # platform
                # state.ident = ident = "connect.hello.%d" % state.count
                # state.count += 1
                # self.spawn(connection_failed_check)
                # message = Message(peer="", subsystem="hello", id=ident, args=["hello"])
                # self.connection.send_vip_object(message)

            def hello_response(sender, version: str = "", router: str = "", identity: str = ""):
                ...
                # _log.info(f"Connected to platform: identity: {identity} version: {version}")
                # _log.debug("Running onstart methods.")
                # hello_response_event.set()
                # self.onstart.sendby(self.link_receiver, self)
                # self.configuration.sendby(self.link_receiver, self)
                # if running_event is not None:
                #     running_event.set()

            return connection_failed_check, hello, hello_response

    def build(self, credentials: Credentials, owner: Agent = None) -> CoreLoop:
        return self.CoreInstance(owner=owner, credentials=credentials, connection_factory=ConnectionFactoryInstance())


#core(Core, CoreInstance, "tcp://127.0.0.1:22916")
