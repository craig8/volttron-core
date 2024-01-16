from __future__ import annotations
from json import JSONDecodeError
import logging
from typing import Any
import struct

from volttron.utils import jsonapi

_log = logging.getLogger(__name__)

ENCODE_FORMAT = "ISO-8859-1"


def deserialize_frames(frames: list[bytes]) -> list:
    decoded = []

    for x in frames:
        if isinstance(x, list):
            decoded.append(deserialize_frames(x))
        elif isinstance(x, int):
            decoded.append(x)
        elif isinstance(x, float):
            decoded.append(x)
        elif isinstance(x, bytes):
            decoded.append(x.decode(ENCODE_FORMAT))
        elif isinstance(x, str):
            decoded.append(x)
        elif x is not None:
            if x == {}:
                decoded.append(x)
                continue
            try:
                d = x.decode(ENCODE_FORMAT)
            except UnicodeDecodeError as e:
                _log.error(f"Unicode decode error: {e}")
                decoded.append(x)
                continue
            try:
                decoded.append(jsonapi.loads(d))
            except JSONDecodeError:
                decoded.append(d)
    return decoded


def serialize_frames(data: list[Any]) -> list[bytes]:
    frames = []

    for x in data:
        try:
            if isinstance(x, list) or isinstance(x, dict):
                frames.append(jsonapi.dumps(x).encode(ENCODE_FORMAT))
            elif isinstance(x, bytes):
                frames.append(x)
            elif isinstance(x, bool):
                frames.append(struct.pack("?", x))
            elif isinstance(x, int):
                frames.append(struct.pack("I", x))
            elif isinstance(x, float):
                frames.append(struct.pack("f", x))
            elif x is None:
                frames.append(None)
            else:
                frames.append(x.encode(ENCODE_FORMAT))
        except TypeError as e:
            import sys
            sys.exit(0)
        except AttributeError as e:
            import sys
            sys.exit(0)
    return frames
