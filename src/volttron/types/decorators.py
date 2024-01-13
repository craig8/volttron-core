"""
decorators.py
=============

This module contains a factory registration function and several instances of it. It also
includes a function for logging traces.
"""
import logging
import inspect
from typing import TypeVar


def factory_registration(name: str):
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
        if hasattr(cls, 'Meta'):
            name = cls.Meta.name

        print(f"Registering {cls.__name__} as a {name}")
        if name in register.registry:
            raise ValueError(f"Name {name} already in register for {register.name}.")
        register.registry[name] = cls
        return cls

    register.name = name
    register.registry = {}
    return register


messagebus = factory_registration("messagebus")
core = factory_registration("core")
connection = factory_registration("connection")
service = factory_registration("service")
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
        raise ValueError(f"No {registration.name} is currently registered")

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
def get_messagebus_instance(name=None) -> object:
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
