from __future__ import annotations
import logging
from typing import TYPE_CHECKING

import gevent
from gevent import Greenlet

from volttron.types.auth.credentials import Credentials
from volttron.types.errors import MessageBusConnectionError
from volttron.client.vip.agent import Agent
#if TYPE_CHECKING:

_log = logging.getLogger(__name__)


class ServiceInterface(Agent):

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     #self.server_config = server_config

    @classmethod
    def get_kwargs_defaults(cls) -> dict[str, any]:
        """
        Class method that allows the specific class to have the ability to specify
        what service arguments are available as defaults.
        """
        return {}

    def set_credential(self, credential: Credentials):
        self._credential = credential
