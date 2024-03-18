from __future__ import annotations

import weakref
from abc import ABC, ABCMeta, abstractmethod, abstractproperty
from subprocess import Popen
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from volttron.types.auth.auth_credentials import Credentials
from volttron.types.message import Message

if TYPE_CHECKING:
    from volttron.server.server_options import ServerOptions


class AbstractCore(ABC):

    @abstractmethod
    def setup(self):
        ...

    @abstractmethod
    def loop(self, running_event):
        ...

    @abstractmethod
    def send_vip(self, message: Message):
        ...


class AbstractAgent(ABC):

    ...
    # @abstractproperty
    # def core(self) -> weakref[AbstractCore]:
    #     ...


class CoreLoop(ABC):

    @abstractmethod
    def loop(self, running_event):
        ...


class AgentBuilder(ABC):

    @abstractmethod
    def build_agent(**kwargs):
        ...


class AgentInstaller(ABC):

    @abstractmethod
    def install_agent(**kwargs):
        ...

    @abstractmethod
    def uninstall_agent(**kwargs):
        ...


class AgentExecutor(ABC):

    @abstractmethod
    def execute(identity: str) -> Popen:
        ...

    @abstractmethod
    def stop():
        ...


class AgentStarter(ABC):

    @abstractmethod
    def start(agent: AbstractAgent):
        ...

    @abstractmethod
    def stop():
        ...


class ConnectionFactory(ABC):

    @abstractproperty
    def address(self) -> str:
        ...

    @abstractmethod
    def create_connection(credentials: Credentials) -> Connection:
        ...


class CoreFactory(ABC):
    ...


class Connection(ABC):

    @abstractproperty
    def connected(self) -> bool:
        ...

    @abstractmethod
    def connect():
        ...

    @abstractmethod
    def disconnect():
        ...

    @abstractmethod
    def is_connected() -> bool:
        ...

    @abstractmethod
    def send_vip_message(message: Message):
        ...

    @abstractmethod
    def recieve_vip_message() -> Message:
        ...


class MessageBus(ABC):

    @abstractmethod
    def start(options: ServerOptions):
        ...

    @abstractmethod
    def stop():
        ...

    @abstractmethod
    def is_running() -> bool:
        ...

    @abstractmethod
    def send_vip_message(message: Message):
        ...

    @abstractmethod
    def receive_vip_message():
        ...


class Service(ABC):
    ...
