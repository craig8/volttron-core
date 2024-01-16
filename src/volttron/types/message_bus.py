from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional
from pathlib import Path
from abc import abstractmethod
from volttron.types.auth.authentication import Authenticator
from volttron.types.auth.authorization import Authorizer
from volttron.types.auth.credentials import CredentialManager

from volttron.types.message import Message


@dataclass
class MessageBusParameters:
    connection_parameters: ConnectionParameters
    credential_manager: CredentialManager = None
    authorizer: Authorizer = None
    authenticator: Authenticator = None

    def has_auth(self) -> bool:
        """Returns true if auth_service is set to something besides None

        :return: true if auth_service set
        :rtype: bool
        """
        return self.auth_service is not None

    @staticmethod
    def load_from_config_file(config_file: str | Path = None,
                              section: str = "volttron") -> MessageBusParameters:
        """
        Attempt to load the parameters from the configuration file.  The standard
        configuration file is assumed with the section volttron.  If the config_file
        is not specified then assumes the config_file within the VOLTTRON_HOME directory
        if that is not found then will return an MessageBusParameters object with
        no parameters sepcified.

        :param config_file: A path to the config file to load, defaults to None
        :type config_file: str | Path, optional
        :param section: A section in the config file to load parameters from.
        :type section: str
        """
        params = MessageBusParameters()
        return params


instance: MessageBusInterface = None


class MessageBusInterface:
    """
    The MessageBusInterface is an abstract base class that defines the interface for a message bus.
    It uses the Singleton metaclass to ensure that only one instance of any class that inherits from it can be created.

    Subclasses must implement the `get_default_parameters`, `get_config_name`, `stop` and `start` methods.

    :method get_default_parameters: This method should return a default set of parameters for use when starting the message bus.
    :method get_config_name: This method should return the name of the message bus. This is used to validate what is started in the config file during dynamic loading of the message bus.
    :method start: This method should start the information flow between volttron and the message bus.
    """

    @abstractmethod
    def build_parameters(self, runtime: "ServerRuntime") -> MessageBusParameters:
        pass

    @abstractmethod
    def get_config_name(cls) -> str:
        """
        Retrieve the name of the messagebus.  This is used to validate what
        is started in the config file during dynamic loading of the messagebus.

        :return: A unique name of messagebus
        :rtype: str
        """
        pass

    @abstractmethod
    def start(self, params: MessageBusParameters):
        """
        Start the information flow between volttron and the message bus.

        :param params: Parameters to be used when starting the message bus.
        :type params: MessageBusParameters
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stop the information flow between volttron and the message bus.
        """
        pass

    @classmethod
    def instance(cls) -> MessageBusInterface:
        global instance
        if not instance:
            from volttron.server.server_options import ServerRuntime
            instance = (ServerRuntime.get_message_bus_cls())()
        return instance

    @abstractmethod
    def is_running(self) -> bool:
        pass

    @abstractmethod
    def send_vip_message(self, message: Message):
        pass

    @abstractmethod
    def receive_vip_message(self) -> Message:
        pass

    # def get_service_credentials(self) -> Credentials:
    #     """

    #     :return:
    #     """
    #     raise NotImplementedError()

    # def get_server_credentials(self) -> Credentials:
    #     """
    #     This method is used in the initial setup of the platform and the server side services.
    #     The credentials of the server should be separate from the agents connecting to the platform.

    #     :return:
    #         A Credentials volttron.types.credentials.Credentials
    #     """
    #     raise NotImplementedError()

    # @staticmethod
    # def get_default_parameters() -> MessageBusParameters:
    #     raise NotImplementedError()
