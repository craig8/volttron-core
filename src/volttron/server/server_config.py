from __future__ import annotations

import inspect
import logging
import os
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml
from volttron.types.credentials import Credentials
#from volttron.types.server_options import ServerRuntime
from volttron.types.service import ServiceInterface
from volttron.utils import get_subclasses

# import volttron.server.aip as aipModule
_log = logging.getLogger(__name__)


def __all_ready_set__(property_name: str, value: Any):
    if value is not None:
        raise f"{property_name} has already been set and cannot be changed."


def __not_set__(property_name: str, value: Any):
    if not value:
        raise ValueError(f"{property_name} has not been set yet!")


@dataclass
class _ServiceConfigs:
    service_config_file: Path
    service_credentials: Credentials
    server_credentials: Credentials

    def __post_init__(self):
        from volttron.server.serviceloader import discover_services
        self._loaded = {}
        if self.service_config_file.exists():
            self._loaded = yaml.safe_load(self.service_config_file.read_text().replace(
                "$volttron_home", os.environ['VOLTTRON_HOME']))

        self._namespace = self._loaded.get('namespace', 'volttron.services')
        self._discovered_services = discover_services(self._namespace)
        self._plugin_map = {}
        self._config_map = {}
        self._identity_map = {}
        self._instances = {}

        for mod_name in self._discovered_services:
            try:
                cls = get_subclasses(mod_name, ServiceInterface)[0]
                identity = mod_name.replace("services", "platform")
                self._identity_map[mod_name] = identity
                self._plugin_map[mod_name] = cls
                self._config_map[mod_name] = self._loaded.get(mod_name, {})

            except ValueError:
                continue

        # self.__auth_file__: Optional[PathLike] = None
        # self.__protected_topics_file__: Optional[PathLike] = None
        # self.__service_config_dict__: Dict = {}
        # self.__internal_address__: Optional[str] = None
        # self.__opts__ = None

    def init_services(self, aip: "AIPplatform"):
        """
        Instantiate all the services available in the volttron.services namespace.
        :return:
        """

        for service_name, service_cls in self._plugin_map.items():
            # Look for parameter with server_config as an argument and pass that in if available
            # otherwise just pass kwargs
            params = inspect.signature(service_cls.__init__).parameters

            config = self._config_map.get(service_name)
            kwargs = {
                "credentials": self.service_credentials,
                "server_credentials": self.server_credentials,
                "identity": self._identity_map[service_name],
                "address": "inproc://vip"
            }
            for arg_name, arg_value in params.items():
                #arg_name, arg_value = arg
                if arg_name in config and arg_name != 'kwargs':
                    kwargs[arg_name] = config[arg_name]
                elif arg_name in config.get('kwargs', {}):
                    kwargs[arg_name] = config.get('kwargs')[arg_name]
                elif arg_name == 'aip':
                    kwargs[arg_name] = aip
            _log.info(f"Creating {service_name}")
            if service_name != 'volttron.services.auth':
                self._instances[service_name] = service_cls(**kwargs)

    def get_service_identity(self, service_name) -> str:
        return self._identity_map.get(service_name)

    def get_service_names(self) -> List[str]:
        return list(self._plugin_map.keys())

    def get_service(self, name: str) -> Type[ServiceInterface]:
        return self._plugin_map.get(name, None)

    def get_service_instance(self, name: str) -> ServiceInterface:
        return self._instances.get(name, None)

    def store_service_configs(self):
        pass
        # with self.service_config_file.open("wt") as fp:
        #     yaml.dump(self.)

    # @property
    # def opts(self):
    #     __not_set__("opts", self.__opts__)
    #     return self.__opts__
    #
    # @opts.setter
    # def opts(self, value):
    #     __all_ready_set__("opts", self.__opts__)
    #     self.__opts__ = value
    #
    # @property
    # def internal_address(self) -> str:
    #     __not_set__("internal_address", self.__internal_address__)
    #     return self.__internal_address__
    #
    # @internal_address.setter
    # def internal_address(self, value):
    #     __all_ready_set__("internal_address", self.__internal_address__)
    #     self.__internal_address__ = value
    #
    # @property
    # def service_config_file(self):
    #     __not_set__("service_config_file", self.__service_config_file__)
    #     return self.__service_config_file__
    #
    # @service_config_file.setter
    # def service_config_file(self, value: PathLike):
    #     __all_ready_set__("service_config_file", self.__service_config_file__)
    #     if isinstance(value, str):
    #         value = Path(value)
    #     if not value.exists():
    #         raise ValueError(f"File {value} does not exists.")
    #     self.__service_config_file__ = value
    #
    # # @property
    # # def aip(self) -> aipModule.AIPplatform:
    # #     __not_set__("aip", self.__aip__)
    # #     return self.__aip__
    # #
    # # @aip.setter
    # # def aip(self, value: aipModule.AIPplatform):
    # #     if self.__aip__ is not None:
    # #         raise ValueError("AIP has already been set and cannot be changed")
    # #     self.__aip__ = value
    #
    # def get_service_enabled(self, service_name: str) -> bool:
    #     self.__init_service_dict__()
    #     service = self.__service_config_dict__.get(service_name)
    #     # Services don't have to be listed in the service_config.yml file so only if there is a
    #     # service listed do we consider whether they are enabled or not.
    #     retval = True
    #     if service is not None and "enabled" in service:
    #         retval = service["enabled"]
    #     return retval
    #
    # def get_services_with_path(self) -> List[str]:
    #     self.__init_service_dict__()
    #     retval: List[str] = []
    #     for service_name, value in self.__service_config_dict__.items():
    #         if 'path' in value:
    #             retval.append(service_name)
    #     return retval
    #
    # def get_service_path(self, service_name: str) -> str:
    #     self.__init_service_dict__()
    #     service = self.__service_config_dict__.get(service_name, {})
    #     # Error condition because services shouldn't be calling this without
    #     # calling the get_services with path above so this should not happen
    #     if service is None or 'path' not in service:
    #         raise ValueError(f'path not defined in service name {service_name}')
    #
    #     return service['path']
    #
    # def get_service_kwargs(self, service_name: str) -> Dict:
    #     self.__init_service_dict__()
    #     service = self.__service_config_dict__.get(service_name, {})
    #     return {} if service is None else service.get("kwargs", {})
    #
    # def __init_service_dict__(self):
    #     if not self.__service_config_dict__:
    #         self.__service_config_dict__ = yaml.safe_load(self.__service_config_file__.open())
    #
    # @property
    # def protected_topics_file(self) -> PathLike:
    #     return self.__protected_topics_file__
    #
    # @protected_topics_file.setter
    # def protected_topics_file(self, value: PathLike):
    #     __all_ready_set__("protected_topics_file", self.__protected_topics_file__)
    #     if isinstance(value, str):
    #         value = Path(value)
    #     self.__protected_topics_file__ = value
    #
    # @property
    # def auth_file(self) -> PathLike:
    #     __not_set__("auth_file", self.__auth_file__)
    #     return self.__auth_file__
    #
    # @auth_file.setter
    # def auth_file(self, value: PathLike):
    #     __all_ready_set__("auth_file", self.__auth_file__)
    #     if isinstance(value, str):
    #         value = Path(value)
    #     self.__auth_file__ = value


# ServiceConfigs = _ServiceConfigs()
