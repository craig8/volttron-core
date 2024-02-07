from __future__ import annotations
import argparse
from collections import OrderedDict

import configparser
from configparser import ConfigParser
import logging
import os
import socket
from configparser import ConfigParser
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import TYPE_CHECKING, Type

import gevent

from volttron.types.singleton import Singleton
if TYPE_CHECKING:
    from volttron.types.protocols import MessageBus
    from volttron.decorators import get_messagebus_class, get_messagebus_instance, get_service_instance, get_service_startup_order
    from volttron.server.serviceloader import ServiceData

_log = logging.getLogger(__name__)


class MultiOrderedDict(OrderedDict):

    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super().__setitem__(key, value)


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
class ServerOptions(Singleton):
    """
    A data class representing the configuration options for a Volttron platform server.

    :ivar volttron_home: The path to the root directory of the Volttron instance.
                         Default is '~/.volttron', which is expanded to the current user's home directory.
    :vartype volttron_home: Union[pathlib.Path, str]

    :ivar instance_name: The name of the Volttron instance. Default is the hostname of the machine.
    :vartype instance_name: str

    :ivar address: A list of addresses on which the platform should listen for incoming connections.
                     Default is None.
    :vartype address: List[str]

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
    volttron_home: Path | str = field(default=Path(os.environ.get('VOLTTRON_HOME', "~/.volttron")).expanduser())
    instance_name: str = None
    address: list[str] = field(default_factory=list)
    agent_isolation_mode: bool = False
    # Module that holds the zmq based classes, though we shorten it assumeing
    # it's in volttron.messagebus
    messagebus: str = "zmq"
    auth_enabled: bool = True

    services: list[ServiceData] = field(default_factory=list)

    def __post_init__(self):
        """
        Initializes the instance after it has been created.

        If `volttron_home` is a string, it is converted to a `pathlib.Path` object.

        If `instance_name` is None, it is set to the hostname of the machine.
        """
        #from volttron.server.serviceloader import ServiceData

        if os.environ.get('VOLTTRON_HOME'):
            self.volttron_home = Path(os.environ.get('VOLTTRON_HOME')).expanduser()
        if isinstance(self.volttron_home, str):
            self.volttron_home = Path(self.volttron_home)
        # Should be the only location where we create VOLTTRON_HOME
        if not self.volttron_home.is_dir():
            self.volttron_home.mkdir(mode=0o755, exist_ok=True, parents=True)
        if self.instance_name is None:
            self.instance_name = socket.gethostname()

        if isinstance(self.address, str):
            self.address = [self.address]
        elif not self.address:
            self.address = ["tcp://127.0.0.1:22916"]

        namespace = "volttron.services"
        #discovered_services = discover_services(namespace)

        # for mod_name in discovered_services:

        #     try:
        #         cls = get_subclasses(mod_name, ServiceInterface)[0]
        #         # Use platform as the default for identities.
        #         identity = mod_name.replace("volttron.services", "platform")
        #         data = ServiceData(mod_name, identity)
        #         self.services.append(data)
        #     except ValueError:
        #         _log.warning(
        #             f"Couldn't find a ServiceInterface class in {mod_name} from discovered_services"
        #         )

    def update(self, opts: argparse.Namespace | dict):
        """Update the opts from the passed command line or a dictionary.

        :param opts: Parameters passed from the command line or a dictionary form volttron testing framework.
        :type opts: argparse.Namespace | dict
        """
        if isinstance(opts, dict):
            self.__dict__.update(opts)
        else:
            self.__dict__.update(opts.__dict__)

    def store(self, file: Path):
        """
        Stores the current configuration options to a file.

        :param file: The path to the file where the configuration options should be stored.
        :type file: Union[pathlib.Path, str]
        """
        parser = ConfigParser(dict_type=MultiOrderedDict, strict=False)

        parser.add_section("volttron")

        kwargs = {}

        services_field = None
        # Store the config options first.
        for field in fields(ServerOptions):
            try:
                # Don't save volttron_home within the config file.
                if field.name not in ('volttron_home', 'services'):
                    # More than one address can be present so we must be careful
                    # with it.
                    if field.name == 'address':
                        parser.set("volttron", "address", "\n".join(getattr(self, field.name)))
                        # for v in getattr(self, field.name):
                        #     parser.set("volttron", "address", v)
                    else:
                        parser.set("volttron", field.name.replace('_', '-'), str(getattr(self, field.name)))
            except configparser.NoOptionError:
                pass

        parser.add_section('services')
        for sd in self.services:
            parser.set("services", sd.identity, sd.klass_path)

            if sd.args:
                parser.add_section(sd.klass_path)
                for arg, value in sd.args:
                    parser.set(sd.klass_path, arg, value)

        parser.write(file.open("w"))

    @staticmethod
    def from_file(file: Path | str = None):
        """
        Creates a `ServerOptions` instance from a file.

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
            parser = ConfigParser(dict_type=MultiOrderedDict, strict=False)
            parser.read(file)

            kwargs = {}

            for field in fields(ServerOptions):
                try:
                    value = parser.get(section="volttron", option=field.name.replace('_', '-'))
                    if value == 'None':
                        value = None
                    elif value == 'False' or value == 'True':
                        value = eval(value)
                    elif field.name == 'service_config' or field.name == 'volttron_home':
                        value = Path(value)
                    elif field.name == 'address':
                        value = value.split('\n')
                    kwargs[field.name] = value
                except configparser.NoOptionError:
                    pass

            options = ServerOptions(**kwargs)
        else:
            options = ServerOptions()
            options.store(file)

        return options


def run_server(config_options: ServerOptions, command_line_args: argparse.Namespace):

    pass


class ServerRuntime:
    _instance: ServerRuntime = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, config_options: ServerOptions, cmdline_args: argparse.Namespace):

        self._config_options = config_options
        self._cmdline_opts = cmdline_args
        self._cred_manager_cls = None
        self._messagebus_instance: MessageBusProtocol = None
        #  get_class(*split_module_class(opts.credential_manager))
        # self._messagebus_cls: MessageBusInterface = None
        # self._messagebus_instance: MessageBusInterface = None
        # subclasses = get_subclasses_of_classpath(
        #     f"{MessageBusInterface.__module__}.{MessageBusInterface.__name__}")

        # for sc in subclasses:
        #     if sc.get_config_name() == opts.message_bus:
        #         self._messagebus_cls = sc
        #         break

        # if not self._messagebus_cls:
        #     raise RuntimeError("No Messagebus found to start!")

        # self._messagebus_instance = self._messagebus_cls()

    def get_messagebus_class(self) -> type[MessageBusProtocol]:
        return get_messagebus_class()

    @property
    def options(self) -> ServerOptions:
        return self._config_options

    def start_messagebus(self) -> MessageBusProtocol:
        if self._messagebus_instance is None:
            mb = get_messagebus_instance()
            mb.start(self)
            self._messagebus_instance = mb
        return self._messagebus_instance

    def run_server(self) -> None:
        greenlets = []

        for lookup in get_service_startup_order():
            instance = get_service_instance(lookup)
            _log.debug(f"Starting {lookup}")
            event = gevent.event.Event()
            task = gevent.spawn(instance.core.run, event)
            event.wait()
            del event
            greenlets.append(task)

        # If one exits then shutdown the server.
        gevent.wait(greenlets, count=1)

    def shutdown_messagebus(self):
        if self._messagebus_instance:
            self._messagebus_instance.stop()

        self._messagebus_instance = None


# reals = ServerRuntime.create()
# AIP = AIPplatform(runtime=ServerRuntime)
# AIP.setup()

# class _ObjectManager:

#     def __init__(self, runtime: ServerRuntime) -> None:
#         self._runtime = runtime
#         #from volttron.server.serviceloader import discover_services
#         # self._loaded = {}

#         # self._namespace = self._loaded.get('namespace', 'volttron.services')
#         # self._discovered_services = discover_services(self._namespace)
#         # self._plugin_map = {}
#         # self._config_map = {}
#         # self._identity_map = {}
#         # self._instances = {}
#         # self._objects = {}

#         # for mod_name in self._discovered_services:
#         #     try:
#         #         cls = get_subclasses(mod_name, ServiceInterface)[0]
#         #         identity = mod_name.replace("services", "platform")
#         #         self._identity_map[mod_name] = identity
#         #         self._plugin_map[mod_name] = cls
#         #         self._config_map[mod_name] = self._loaded.get(mod_name, {})

#         #     except ValueError:
#         #         continue

#     def init_services(self):
#         import inspect
#         for mod_name, cls in self._plugin_map.items():
#             config = cls.get_kwargs_defaults()
#             print(f"Creating instance for {mod_name}")
#             argspec = inspect.getfullargspec(cls.__init__)
#             print(argspec)
#             args = []
#             for arg in argspec.args:
#                 if arg == 'self':
#                     continue

#                 try:
#                     args.append(ObjectManager.get_object(arg))
#                 except KeyError:
#                     _log.error(
#                         f"Missing argument to service from ObjectManager '{arg}' not found for module '{mod_name}'"
#                     )
#                     raise

#             if args:
#                 self._objects[mod_name] = cls(*args,
#                                               identity=self._identity_map[mod_name],
#                                               address=self._runtime.options.address)
#             else:
#                 self._objects[mod_name] = cls(identity=self._identity_map[mod_name],
#                                               address=self._runtime.options.address)

#     def get_service(self, service_name: str) -> ServiceInterface:
#         try:
#             return self._objects[service_name]
#         except KeyError:
#             try:
#                 for k, v in self._identity_map.items():
#                     if v == service_name:
#                         return self._objects[k]
#                 raise KeyError(service_name)
#             except KeyError:
#                 _log.error(f"Could not find service: {service_name}")
#                 raise

#     # def create_service(self):
#     #     pass

#     # def stop_service(self):
#     #     pass

#     def get_available_services(self) -> List[str]:
#         return list(self._identity_map.values())

#     # def discover_services(self):
#     #     pass

#     def get_object(self, key) -> object:
#         return self._objects[key]

#     def get_objects(self) -> List[str]:
#         return list(self._objects.keys())

#     def create_instance(self, clasz, key: str = None, **kwargs) -> object:
#         if isinstance(clasz, str):
#             mod, clsdef = split_module_class(clasz)
#             cls = get_class(mod, clsdef)
#         else:
#             cls = clasz

#         if key is not None:
#             obj = self._objects[key] = cls(**kwargs)
#         else:
#             obj = self._objects[clasz] = cls(**kwargs)
#         return obj

# ObjectManager = _ObjectManager(ServerRuntime)
