from __future__ import annotations

from typing import Protocol, runtime_checkable

from volttron.types.message import Message


@runtime_checkable
class ConnectionProtocol(Protocol):

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
class MessageBusProtocol(Protocol):
    # TODO: Change to runtime stuff.
    def start(runtime: object):
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
class ServiceProtocol(Protocol):

    def start(**kwargs):
        ...


@runtime_checkable
class RequiresServiceIdentityProtocol(ServiceProtocol, Protocol):

    def requires() -> list[str] | None:
        ...
