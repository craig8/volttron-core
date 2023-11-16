from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
import sys
from copy import copy
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Dict, KeysView, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from volttron.types.server_options import ServerRuntime, ServiceConfigs

from volttron.types.service import ServiceInterface
from volttron.utils import get_class, get_module, get_subclasses

_log = logging.getLogger(__name__)

__discovered_plugins__: Dict[str, Tuple] = {}
__namespaces__: Set[str] = set()
__required_plugins__: Set[str] = set()
__plugin_startup_order__: List[str] = ["volttron.services.config_store"]
__disabled_plugins__: Set[str] = {
    'volttron.services.health', 'volttron.services.routing', 'volttron.services.peer',
    'volttron.services.external'
}

__all__ = ["get_service_names", "init_services", "discover_services", "get_service_instance"]

__service_interface_class__ = get_class('volttron.types.service', 'ServiceInterface')

__started_services__: Dict[str, ServiceInterface] = {}
__service_instances__: Dict[str, ServiceInterface] = {}


def get_service_names() -> KeysView[str]:
    return __discovered_plugins__.keys()


def start_service(service_name: str):
    service_interface = get_class('volttron.types', 'ServiceInterface')
    module = get_module(service_name)
    subclasses = get_subclasses(module, service_interface)
    service = subclasses[0](serverkey=None,
                            identity="platform.web",
                            bind_web_address="http://127.0.0.1:8080")
    __started_services__[service_name] = service
    greenlet = service.spawn_in_greenlet()
    return greenlet


def get_service_instance(service_name: str) -> Optional[ServiceInterface]:
    return __service_instances__.get(service_name)


def init_services(runtime: ServerRuntime,
                  config: ServiceConfigs) -> List[Tuple[str, ServiceInterface]]:

    # default_kwargs = dict(enable_store=False,
    #                       address=config.internal_address,
    #                       heartbeat_autostart=True)
    # default_kwargs = dict(address=config.internal_address)

    # First we discover the services in the default namespace for services.
    found = __discover_services__("volttron.services")
    if __disabled_plugins__:
        found = list(set(found) - set(__disabled_plugins__))

    # Then we loop over the configurations and see if there are any with the
    # path element specified so that we can add them to the path and discover them
    # path_services = config.get_services_with_path()
    #
    # for pname in path_services:
    #     service_path = config.get_service_path(pname)
    #     if service_path not in sys.path:
    #         if not Path(service_path).exists():
    #             raise ValueError(f"path for {pname} {service_path} does not exist.")
    #         sys.path.insert(0, service_path)
    #     __discover_services__(pname)

    def init_plugin(plugin_name, plugin):
        try:
            # if config.get_service_path(plugin_name):
            #     service_path = config.get_service_path(plugin_name)
            #     if service_path not in sys.path:
            #         sys.path.insert(0, service_path)
            #
            #     plugins = discover_services(plugin_name)
            #     if not plugins:
            #         raise ValueError(f"Invalid service detected {plugin_name} with path {service_path}")
            #     module = plugins[0]
            # else:
            module = plugin

            kwargs = copy(default_kwargs)
            subclasses = get_subclasses(module, __service_interface_class__, return_all=True)
            kwargs.update(config.get_service_kwargs(plugin_name))
            if "identity" not in kwargs:
                kwargs["identity"] = plugin_name.replace("volttron.services", "platform")
            # TODO allow multiple subclasses in file suppport.
            for sub in subclasses:
                # Look for parameter with server_config as an argument and pass that in if available
                # otherwise just pass kwargs
                params = inspect.signature(sub.__init__).parameters
                if 'server_config' in params.keys():
                    instance = sub(server_config=config, **kwargs)
                else:
                    _log.debug(f"{plugin_name} does not take a server_config as first param.")
                    instance = sub(**kwargs)
                # try:
                #     instance = sub(server_config=config, **kwargs)
                # except TypeError:
                #     _log.debug(f"{plugin_name} does not take a server_config as first param.")
                #     instance = sub(**kwargs)
                __service_instances__[plugin_name] = instance
                return instance
        except ValueError as ex:
            _log.warning(ex.args)

    inited_services = []

    for plugin_name in __plugin_startup_order__:
        if plugin_name not in found:
            raise ValueError(f"Invalid plugin specified in plugin_startup_order {plugin_name}")
        _log.info(f"Init plugin: {plugin_name}, {__discovered_plugins__[plugin_name]}")
        if plugin_name not in __disabled_plugins__:
            plugin = __discovered_plugins__.pop(plugin_name)
            inited_services.append((plugin_name, init_plugin(plugin_name, plugin)))

    for plugin_name, plugin in __discovered_plugins__.items():
        if plugin_name not in __plugin_startup_order__ and plugin_name not in __disabled_plugins__:
            if config.get_service_enabled(plugin_name):
                _log.info(f"Init plugin {plugin_name}, {plugin}")
                service = init_plugin(plugin_name, plugin)
                # Only add service to the list if the service has the correct interface.
                if service is not None:
                    inited_services.append((plugin_name, service))
            else:
                _log.debug(f"Plugin {plugin_name} not enabled.")

    return inited_services


def discover_services(namespace: str) -> List[str]:
    module = importlib.import_module(namespace)
    return __discover_services__(module)


def __iter_namespace__(ns_pkg):
    """
    Uses namespace package to locate all namespaces with the ns_pkg as its root.

    For example in our system any namespace package that starts with volttron.services
    should be detected.

    NOTE: NO __init__.py file should ever be located within any package volttron.services or
            the importing will break

    @param: ns_pkg: Namespace to search for modules in.
    """
    # Specifying the second argument (prefix) to iter_modules makes the
    # returned name an absolute name instead of a relative one. This allows
    # import_module to work without having to do additional modification to
    # the name.
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


def __discover_services__(namespace: str | ModuleType) -> List[str]:
    """
    Map all of the discovered namespaces to the volttron.services import.  Build
    a dictionary 'package' -> module.
    """
    if isinstance(namespace, str):
        namespace = importlib.import_module(namespace)

    # Add the namespace that is searched in case we need to load others in the future.
    __namespaces__.add(namespace.__name__)
    found: List[str] = []
    for finder, name, ispkg in __iter_namespace__(namespace):
        found.append(name)
        __discovered_plugins__[name] = importlib.import_module(name)
    return found


# """
# Manage the startup order of plugins available.  Note an error will
# be raised and the server will not startup if the plugin doesn't exist.
# The plugins that are within this same codebase hold the "default" services
# that should always be available in the system.  VOLTTRON requires that
# the services be started in a specific order for its processing to work as
# intended.
# """
# plugin_startup_order = [
#     "volttron.services.config_store",
#     "volttron.services.auth",
# ]
#
# plugin_disabled = ["volttron.services.health"]
#
# for p in plugin_startup_order:
#     if p not in __discovered_plugins__:
#         raise ValueError(f"Invalid plugin specified in plugin_startup_order {p}")
#     _log.info(f"Starting plugin: {p}, {__discovered_plugins__[p]}")
#
# for p, v in __discovered_plugins__.items():
#     if p not in plugin_startup_order and p not in plugin_disabled:
#         _log.info(f"Starting plugin {p}, {v}")
