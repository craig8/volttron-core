from dataclasses import dataclass, field
from typing import Any, Optional

from dataclass_wizard import JSONSerializable


@dataclass(frozen=True)
class Message(JSONSerializable):
    subsystem: str
    recipient: Optional[str] = None
    peer: Optional[str] = None
    user: str = ''
    msg_id: str = ''
    args: list[any] = field(default_factory=list)
    via: Optional[str] = None
