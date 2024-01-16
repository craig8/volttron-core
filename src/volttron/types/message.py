from __future__ import annotations
from typing import Any
from volttron.utils.frame_serialization import serialize_frames as serialize_bytes, deserialize_frames as deserialize_bytes
from dataclasses import dataclass, field
from volttron.utils import jsonapi
from dataclass_wizard import JSONSerializable


@dataclass(frozen=True)
class Message(JSONSerializable):
    recipient: str
    sender: str = ''
    peer: str = ''
    subsystem: str = ''
    id: str = ''
    user_id: str = ''
    signature: str = 'VIP1'
    args: list[Any] = field(default_factory=list)

    # def serialize_to_bytes(self) -> bytes:
    #     byte_array = serialize_bytes([self.peer, self.subsystem, self.id, self.args])
    #     return b"".join(byte_array)

    # def deserialize_from_bytes(self, data: bytes) -> None:
    #     results = deserialize_bytes(data)
    #     self.peer, self.subsystem, self.id, self.args = results

    # def serialize_to_json(self) -> str:
    #     return jsonapi.dumps(self.__dict__)

    # @staticmethod
    # def load_from_bytes(data: bytes) -> Message:
    #     m = Message("", "", "", [])
    #     m.deserialize_from_bytes(data)
    #     return m

    # @staticmethod
    # def load_from_json(data: str) -> Message:
    #     m = Message("", "", "", [])
    #     m.__dict__ = jsonapi.loads(data)
    #     return m
