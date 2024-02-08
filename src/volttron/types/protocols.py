from __future__ import annotations

from typing import Protocol, runtime_checkable, TYPE_CHECKING

from volttron.types.message import Message

if TYPE_CHECKING:
    from volttron.server.run_server import ServerOptions


@runtime_checkable
class Connection(Protocol):

    def connect(**kwargs):
        ...

    def disconnect():
        ...

    def is_connected() -> bool:
        ...

    def send_vip_message(message: Message):
        ...

    def recieve_vip_message() -> Message:
        ...


@runtime_checkable
class MessageBus(Protocol):

    def start(options: ServerOptions):
        ...

    def stop():
        ...

    def is_running() -> bool:
        ...

    def send_vip_message(message: Message):
        ...

    def receive_vip_message():
        ...


@runtime_checkable
class Service(Protocol):

    def start(**kwargs):
        ...


@runtime_checkable
class RequiresServiceIdentity(Service, Protocol):

    def requires() -> list[str] | None:
        ...
