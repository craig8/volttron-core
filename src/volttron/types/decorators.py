"""
decorators.py
=============

This module contains a factory registration function and several instances of it. It also
includes a function for logging traces.
"""
import logging
import inspect
from typing import TypeVar
from typing import Protocol
from volttron.types.protocols import (ConnectionProtocol, MessageBusProtocol, ServiceProtocol,
                                      RequiresServiceIdentityProtocol)


def factory_registration(name: str, protocol: Protocol = None):
    """
    Create a factory registration function.

    The function will have a registry attribute that is a dictionary of registered
    classes and a name attribute that is the name of the factory.

    @param name: The name of the factory.
    @type name: str
    @return: The factory registration function.
    @rtype: function
    """

    def register(cls):
        lookup_key = None
        if hasattr(cls, 'Meta'):
            # Meta can either have a name or an identity, but not both.
            # We use either one of the values as a lookup for the register.
            if hasattr(cls.Meta, 'name') and hasattr(cls.Meta, 'identity'):
                raise ValueError("Only name or identity can be specified in Meta.")
            elif hasattr(cls.Meta, 'name'):
                lookup_key = cls.Meta.name
            elif hasattr(cls.Meta, 'identity'):
                lookup_key = cls.Meta.identity

        if protocol is not None and not isinstance(cls, protocol):
            raise ValueError(f"{cls.__name__} doesn't implement {protocol.__name__}")

        print(f"Registering {cls.__name__} as a {lookup_key}")
        if lookup_key in register.registry:
            raise ValueError(f"{lookup_key} already in register for {register.name}.")
        register.registry[lookup_key] = cls
        return cls

    register.name = name
    register.registry = {}
    return register


messagebus = factory_registration("messagebus", protocol=MessageBusProtocol)
core = factory_registration("core")
connection = factory_registration("connection", protocol=ConnectionProtocol)
service = factory_registration("service",
                               protocol=ServiceProtocol | RequiresServiceIdentityProtocol)
authorizer = factory_registration("authorizer")
authenticator = factory_registration("authenticator")
credential_store = factory_registration("credential_store")
auth_create_hook = factory_registration("auth_create_hook")
auth_add_hook = factory_registration("auth_add_hook")
auth_remove_hook = factory_registration("auth_remove_hook")
auth_list_hook = factory_registration("auth_list_hook")

import logging
import inspect


def logtrace(func: callable, *args, **kwargs):
    """
    Decorator that logs the function call and return value.

    Example:
        @logtrace
        def add(a, b):
            return a + b

        add(2, 3)
        # Output in debug log:
        # add(a, b) called with (2, 3), {}
        # add returned: 5

    @param func: The function to be decorated.
    @type func: callable
    @return: The decorated function.
    @rtype: callable
    """
    logger = logging.getLogger(func.__name__)
    sig = inspect.signature(func)

    def do_logging(*args, **kwargs):
        logger.debug(f"{func.__name__}{sig} called with {args}, {kwargs}")
        ret = func(*args, **kwargs)
        logger.debug(f"{func.__name__} returned: {ret}")
        return ret

    return do_logging


def __get_create_instance_from_factory__(instances, registration, name: str = None):
    if not registration.registry:
        raise ValueError(f"No {name} is currently registered")

    if name is None and len(messagebus.registry) > 1:
        raise ValueError(f"Can't figure out which messagebus to return.")

    mb = None
    if name is None:
        # First name of the registry dictionary.
        name = list(messagebus.registry.keys())[0]
        __messagebus__[name] = messagebus.registry[name]()

    mb = __messagebus__.get(name)
    if mb is None:
        raise ValueError(f"Couldn't retrieve {name} from register")
    return mb


def __get_class_from_factory__(registration, name: str = None):
    if not registration.registry:
        raise ValueError(f"No {registration.name} is currently registered")

    if name is None and len(messagebus.registry) > 1:
        raise ValueError(f"Can't figure out which messagebus to return.")

    if name is None:
        # First name of the registry dictionary.
        name = list(messagebus.registry.keys())[0]

    if name not in registration.registry:
        raise ValueError(f"Couldn't retrieve {name} from register")

    return registration.registry.get(name)


__messagebus__: dict[str, object] = {}


@logtrace
def get_messagebus_instance(name=None) -> MessageBusProtocol:
    return __get_create_instance_from_factory__(__messagebus__, messagebus, name)


__messagebus_core__: dict[str, object] = {}


@logtrace
def get_messagebus_core(name=None) -> object:
    return __get_create_instance_from_factory__(__messagebus_core__, core, name)


__messagebus_connection__: dict[str, object] = {}


@logtrace
def get_messagebus_core(name=None) -> object:
    """
    Return a messagebus connection instance.

    :param name: _description_, defaults to None
    :type name: _type_, optional
    :return: _description_
    :rtype: object
    """
    return __get_create_instance_from_factory__(__messagebus_connection__, connection, name)


@logtrace
def get_messagebus_class(name: str = None) -> type:
    """
    Return a registered messagebus class.

    :param name: The name of the registered messagebus class, defaults to None
    :type name: str, optional
    :return: The registered messagebus class
    :rtype: type
    :raises ValueError: If no messagebus class is registered or if the passed name doesn't
        exist in the registry
    """
    return __get_class_from_factory__(messagebus, name)


@logtrace
def get_messagebus_core_class(name=None) -> type:
    """
    Return a registered core class.

    :param name: The name of the registered core class, defaults to None
    :type name: str, optional
    :return: The registered core class
    :rtype: type
    :raises ValueError: If no core class is registered or if the passed name doesn't
        exist in the registry
    """
    return __get_class_from_factory__(messagebus, name)


@logtrace
def get_authorizer_class(name=None) -> type:
    return __get_class_from_factory__(authorizer, name)


@logtrace
def get_authenticator_class(name=None) -> type:
    return __get_class_from_factory__(authenticator, name)


@logtrace
def get_credential_store_class(name=None) -> type:
    return __get_class_from_factory__(credential_store, name)


# @logtrace
# def get_service_classes() -> dict[str, type]:
#     return service.values())


@logtrace
def get_services() -> dict[str, type]:
    return service.registry


@logtrace
def get_services_without_requires() -> list[type]:
    return list(filter(lambda x: not hasattr(x.Meta, "requires"), service.registry.values()))


@logtrace
def get_services_with_requires() -> list[type]:
    return list(filter(lambda x: hasattr(x.Meta, "requires"), service.registry.values()))


@logtrace
def get_service_class(identity: str) -> type:
    return service.registry[identity]


__service_instances__: dict[str, object] = {}


@logtrace
def get_service_instance(identity: str) -> object:
    return __get_create_instance_from_factory__(__service_instances__, service, identity)


@logtrace
def get_service_startup_order() -> list[str]:
    ordered: list[str] = ["platform.config"]

    for lookup, cls in service.registry.items():
        if lookup not in ('platform.config', ):
            ordered.append(lookup)

    return ordered


#    is_required_by: dict[str, list[str]] = {}

# for k, r in service.registry.items():
#     is_required_by[k] = r

# for k, r in service.registry.items():
#     if hasattr(r, "Meta") and hasattr(r.Meta, "requires"):
#         if isinstance(r.Meta.requires, str):
#             r.Meta.requires = [r.Meta.requires]

#         for require in r.Meta.requires:
#             is_required_by[require].append(k)
