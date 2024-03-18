from __future__ import annotations


class ClientContext:

    def __init__(self, identity: str, volttron_home: str):
        self._identity: str = identity
        self._volttron_home: str = volttron_home

    @staticmethod
    def load(identity: str) -> ClientContext:
        pass
