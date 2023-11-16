from __future__ import annotations

import configparser
import logging
import os
import socket
from configparser import ConfigParser
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import ClassVar, List, Type

import yaml

from volttron.server.aip import AIPplatform
from volttron.types.credentials import CredentialsGenerator, CredentialsManager
from volttron.types.message_bus import MessageBusInterface
from volttron.types.service import ServiceInterface
from volttron.utils import get_class
from volttron.utils.dynamic_helper import get_subclasses

_log = logging.getLogger(__name__)


def split_module_class(full_class):
    """
    Splits a fully qualified class name into its module and class name components.

    :param full_class: The fully qualified class name to split.
    :type full_class: str

    :returns: A tuple containing the module name and class name.
    :rtype: Tuple[str, str]

    :raises ValueError: If `full_class` is not a fully qualified class name.
    """
    index = full_class.rindex(".")
    return full_class[:index], full_class[index + 1:]


@dataclass
class _ServerOptions:
    """
    A data class representing the configuration options for a Volttron platform server.

    :ivar volttron_home: The path to the root directory of the Volttron instance.
                         Default is '~/.volttron', which is expanded to the current user's home directory.
    :vartype volttron_home: Union[pathlib.Path, str]

    :ivar instance_name: The name of the Volttron instance. Default is the hostname of the machine.
    :vartype instance_name: str

    :ivar addresses: A list of addresses on which the platform should listen for incoming connections.
                     Default is None.
    :vartype addresses: List[str]

    :ivar agent_isolation_mode: Flag indicating whether the agent isolation mode is enabled.
                                Default is False.
    :vartype agent_isolation_mode: bool

    :ivar message_bus: The fully-qualified name of the message bus class to use. Default is
                       'volttron.messagebus.zmq.ZmqMessageBus'.
    :vartype message_bus: str

    :ivar agent_core: The fully-qualified name of the agent core class to use. Default is
                      'volttron.messagebus.zmq.ZmqCore'.
    :vartype agent_core: str

    :ivar auth_service: The fully-qualified name of the authentication service class to use. Default is
                        'volttron.services.auth'.
    :vartype auth_service: str
    
    :ivar service_config: The Path to the service config file for loading services into the context.
    :vartype service_service: Path
    """
    volttron_home: Path | str = field(default=Path("~/.volttron").expanduser())
    instance_name: str = None
    address: str = "tcp://127.0.0.1:22916"
    agent_isolation_mode: bool = False
    message_bus: str = "volttron.messagebus.zmq.ZmqMessageBus"
    agent_core: str = "volttron.messagebus.zmq.ZmqCore"
    authentication_class: str = "volttron.messagebus.zmq.ZmqAuthentication"
    authorization_class: str = "volttron.messagebus.zmq.ZmqAuthorization"
    auth_service: str = "volttron.services.auth"
    service_config: str = None

    def __post_init__(self):
        """
        Initializes the instance after it has been created.

        If `volttron_home` is a string, it is converted to a `pathlib.Path` object.

        If `instance_name` is None, it is set to the hostname of the machine.
        """
        if os.environ.get('VOLTTRON_HOME'):
            self.volttron_home = Path(os.environ.get('VOLTTRON_HOME')).expanduser()
        if isinstance(self.volttron_home, str):
            self.volttron_home = Path(self.volttron_home)
        # Should be the only location where we create VOLTTRON_HOME
        if not self.volttron_home.is_dir():
            self.volttron_home.mkdir(mode=0o777, exist_ok=True, parents=True)
        if self.instance_name is None:
            self.instance_name = socket.gethostname()
        if self.service_config is None:
            self.service_config = self.volttron_home / "service_config.yml"
        if not isinstance(self.service_config, str):
            self.service_config = Path(self.service_config)

    def store(self, file: Path):
        """
        Stores the current configuration options to a file.

        :param file: The path to the file where the configuration options should be stored.
        :type file: Union[pathlib.Path, str]
        """
        parser = ConfigParser()

        parser.add_section("volttron")

        kwargs = {}

        for field in fields(_ServerOptions):
            try:
                # Don't save volttron_home within the config file.
                if field.name != 'volttron_home':
                    parser.set("volttron", field.name.replace('_', '-'),
                               str(getattr(self, field.name)))
            except configparser.NoOptionError:
                pass

        parser.write(file.open("w"))

    @staticmethod
    def from_file(file: Path | str = None):
        """
        Creates a `_ServerOptions` instance from a file.

        If `file` is None, the default file location ('$VOLTTRON_HOME/config') is used.

        :param file: The path to the file containing the configuration options.
        :type file: Optional[Union[pathlib.Path, str]]

        :returns: A `_ServerOptions` instance created from the file.
        :rtype: _ServerOptions
        """
        if file is None:
            if os.environ.get('VOLTTRON_HOME'):
                file = Path(os.environ.get('VOLTTRON_HOME')).expanduser() / "config"
            else:
                file = Path("~/.volttron/config").expanduser()

        if isinstance(file, str):
            file = Path(file)

        if file.exists():
            parser = ConfigParser()
            parser.read(file)

            kwargs = {}

            for field in fields(_ServerOptions):
                try:
                    value = parser.get(section="volttron", option=field.name.replace('_', '-'))
                    if value == 'None':
                        value = None
                    elif value == 'False' or value == 'True':
                        value = eval(value)
                    elif field.name == 'service_config' or field.name == 'volttron_home':
                        value = Path(value)
                    kwargs[field.name] = value
                except configparser.NoOptionError:
                    pass

            options = _ServerOptions(**kwargs)
        else:
            options = _ServerOptions()
            options.store(file)

        return options


# Global load of options from a config file.
ServerOptions = _ServerOptions.from_file()


class _ServerRuntime:

    def __init__(self, opts: ServerOptions):
        self._opts = opts
        self._cred_manager_cls = None    #  get_class(*split_module_class(opts.credential_manager))
        self._message_bus_cls = get_class(*split_module_class(opts.message_bus))
        self._cred_generator_cls = None    # get_class(*split_module_class(opts.credential_generator))
        self._auth_service_cls = None    # opts.auth_service
        # # There does not have to be an auth service.
        # if opts.auth_service is not None:
        #     self._auth_service_cls = get_class(*split_module_class(opts.auth_service))

    @property
    def options(self) -> ServerOptions:
        return self._opts

    # @property
    # def credential_generator_cls(self) -> Type[CredentialsGenerator]:
    #     return self._cred_generator_cls

    # @property
    # def credential_manager_cls(self) -> Type[CredentialsManager]:
    #     return self._cred_manager_cls

    @property
    def message_bus_cls(self) -> Type[MessageBusInterface]:
        return self._message_bus_cls

    @property
    def auth_service_cls(self):
        return self._auth_service_cls


ServerRuntime = _ServerRuntime(ServerOptions)
AIP = AIPplatform(runtime=ServerRuntime)
AIP.setup()


class _ObjectManager:

    def __init__(self, runtime: ServerRuntime) -> None:
        self._runtime = runtime
        from volttron.server.serviceloader import discover_services
        self._loaded = {}

        if self._runtime.options.service_config.exists():
            self._loaded = yaml.safe_load(self._runtime.options.service_config.read_text().replace(
                "$volttron_home", os.environ['VOLTTRON_HOME']))

        self._namespace = self._loaded.get('namespace', 'volttron.services')
        self._discovered_services = discover_services(self._namespace)
        self._plugin_map = {}
        self._config_map = {}
        self._identity_map = {}
        self._instances = {}
        self._objects = {}

        for mod_name in self._discovered_services:
            try:
                cls = get_subclasses(mod_name, ServiceInterface)[0]
                identity = mod_name.replace("services", "platform")
                self._identity_map[mod_name] = identity
                self._plugin_map[mod_name] = cls
                self._config_map[mod_name] = self._loaded.get(mod_name, {})

            except ValueError:
                continue

    def init_services(self):
        import inspect
        for mod_name, cls in self._plugin_map.items():
            config = cls.get_kwargs_defaults()
            print(f"Creating instance for {mod_name}")
            argspec = inspect.getfullargspec(cls.__init__)
            print(argspec)
            args = []
            for arg in argspec.args:
                if arg == 'self':
                    continue

                try:
                    args.append(ObjectManager.get_object(arg))
                except KeyError:
                    _log.error(
                        f"Missing argument to service from ObjectManager '{arg}' not found for module '{mod_name}'"
                    )
                    raise

            if args:
                self._objects[mod_name] = cls(*args,
                                              identity=self._identity_map[mod_name],
                                              address=self._runtime.options.address)
            else:
                self._objects[mod_name] = cls(identity=self._identity_map[mod_name],
                                              address=self._runtime.options.address)

    def get_service(self, service_name: str) -> ServiceInterface:
        try:
            return self._objects[service_name]
        except KeyError:
            try:
                for k, v in self._identity_map.items():
                    if v == service_name:
                        return self._objects[k]
                raise KeyError(service_name)
            except KeyError:
                _log.error(f"Could not find service: {service_name}")
                raise

    # def create_service(self):
    #     pass

    # def stop_service(self):
    #     pass

    def get_available_services(self) -> List[str]:
        return list(self._identity_map.values())

    # def discover_services(self):
    #     pass

    def get_object(self, key) -> object:
        return self._objects[key]

    def get_objects(self) -> List[str]:
        return list(self._objects.keys())

    def create_instance(self, clasz, key: str = None, **kwargs) -> object:
        if isinstance(clasz, str):
            mod, clsdef = split_module_class(clasz)
            cls = get_class(mod, clsdef)
        else:
            cls = clasz

        if key is not None:
            obj = self._objects[key] = cls(**kwargs)
        else:
            obj = self._objects[clasz] = cls(**kwargs)
        return obj


ObjectManager = _ObjectManager(ServerRuntime)
