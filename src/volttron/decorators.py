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
from volttron.types.protocols import (Connection, MessageBus, Service, RequiresServiceIdentity)
from volttron.types.auth import (AuthService, Authorizer, Authenticator, CredentialsStore, CredentialsManager,
                                 AuthorizationManager)
from volttron.utils.logs import logtrace


def factory_registration(registy_name: str, protocol: Protocol = None):
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
        else:
            lookup_key = cls.__name__

        if lookup_key is None:
            raise ValueError(f"{cls.__name__} does not have an internal Meta class with identity or name.")

        if protocol is not None and not isinstance(cls, protocol):
            raise ValueError(f"{cls.__name__} doesn't implement {protocol}")

        if lookup_key is None:
            print("Lookup key is none!")
        print(f"Registering {cls.__name__} as a {lookup_key}")
        if lookup_key in register.registry:
            raise ValueError(f"{lookup_key} already in register for {register.name}.")
        register.registry[lookup_key] = cls
        return cls

    register.registy_name = registy_name
    register.registry = {}
    return register


messagebus = factory_registration("messagebus", protocol=MessageBus)
core = factory_registration("core")
connection = factory_registration("connection", protocol=Connection)
service = factory_registration("service", protocol=Service | RequiresServiceIdentity)
authservice = factory_registration("authservice", protocol=AuthService)
authorizer = factory_registration("authorizer", protocol=Authorizer)
authenticator = factory_registration("authenticator", protocol=Authenticator)
authorization_manager = factory_registration("authorization_manager", protocol=AuthorizationManager)
credentials_store = factory_registration("credentials_store", protocol=CredentialsStore)
credentials_manager = factory_registration("credentials_manager", protocol=CredentialsManager)
auth_create_hook = factory_registration("auth_create_hook")
auth_add_hook = factory_registration("auth_add_hook")
auth_remove_hook = factory_registration("auth_remove_hook")
auth_list_hook = factory_registration("auth_list_hook")


def __get_create_instance_from_factory__(*, instances, registration, name: str = None, **kwargs):
    if not registration.registry:
        raise ValueError(f"No {registration.registy_name} is currently registered")

    if name is None and len(registration.registry) > 1:
        raise ValueError(f"Can't figure out which messagebus to return.")

    the_instance = None
    if name is None:
        # First name of the registry dictionary.
        name = list(registration.registry.keys())[0]
        signature = inspect.signature(registration.registry[name].__init__)
        for k, v in kwargs.items():
            if k not in signature.parameters:
                raise ValueError(f"Invalid parameter {k} for {name} signature has {signature.parameters}")

        instances[name] = registration.registry[name](**kwargs)
    elif name not in instances:
        instances[name] = registration.registry[name]()

    the_instance = instances.get(name)
    if the_instance is None:
        raise ValueError(f"Couldn't retrieve {name} from register")
    return the_instance


def __get_class_from_factory__(registration, name: str = None):
    if not registration.registry:
        raise ValueError(f"No {registration.name} is currently registered")

    if name is None and len(registration.registry) > 1:
        raise ValueError(f"Can't figure out which messagebus to return.")

    if name is None:
        # First name of the registry dictionary.
        name = list(registration.registry.keys())[0]

    if name not in registration.registry:
        raise ValueError(f"Couldn't retrieve {name} from register")

    return registration.registry.get(name)


__messagebus__: dict[str, object] = {}


@logtrace
def get_messagebus_instance(name=None) -> MessageBus:
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


__authorizer__: dict[str, Authorizer] = {}


@logtrace
def get_authorizer(name: str = None, authorization_manager: AuthorizationManager = None) -> Authorizer:
    authorizer_instance: Authorizer = None
    if name is not None:
        authorizeritem = __authorizer__.get(name, None)

    # Use the default authorization manager if none is provided.
    if authorization_manager is None:
        authorization_manager = get_authorization_manager()

    assert isinstance(authorization_manager, AuthorizationManager)

    if authorizer_instance is None:
        authorizer_instance = __get_create_instance_from_factory__(instances=__authorizer__,
                                                                   registration=authorizer,
                                                                   name=name,
                                                                   authorization_manager=authorization_manager)
        if authorizer_instance is not None:
            __authorizer__[name] = authorizer_instance
    return authorizer_instance


__authenticator__: dict[str, Authenticator] = {}


@logtrace
def get_authenticator(name: str = None, credentials_manager: CredentialsManager = None) -> Authenticator:
    authenticatoritem: Authenticator = None
    if name is not None:
        authenticatoritem = __authenticator__.get(name, None)
    if credentials_manager is None:
        credentials_manager = get_credentials_manager()

    assert isinstance(credentials_manager, CredentialsManager)

    if authenticatoritem is None:
        authenticatoritem = __get_create_instance_from_factory__(instances=__authenticator__,
                                                                 registration=authenticator,
                                                                 name=name,
                                                                 credentials_manager=credentials_manager)
        if authenticatoritem is not None:
            __authenticator__[name] = authenticatoritem
    return authenticatoritem


__credentials_store__: dict[str, CredentialsStore] = {}


@logtrace
def get_credentials_store(name: str = None) -> CredentialsStore:
    credentials_store_item: CredentialsStore = None
    if name is not None:
        credentials_store_item = __credentials_store__.get(name, None)
    if credentials_store_item is None:
        credentials_store_item = __get_create_instance_from_factory__(instances=__credentials_store__,
                                                                      registration=credentials_store,
                                                                      name=name)
        if credentials_store_item is not None:
            __credentials_store__[name] = credentials_store_item
    return credentials_store_item


__authorization_manager__: dict[str, AuthorizationManager] = {}


@logtrace
def get_authorization_manager(name: str = None) -> AuthorizationManager:
    auth_manager: AuthorizationManager = None
    if name is not None:
        auth_manager = __authorization_manager__.get(name, None)
    if auth_manager is None:
        auth_manager = __get_create_instance_from_factory__(instances=__authorization_manager__,
                                                            registration=authorization_manager,
                                                            name=name)
        if auth_manager is not None:
            __authorization_manager__[name] = auth_manager
    return auth_manager


@logtrace
def get_authservice_class(name=None) -> type:
    return __get_class_from_factory__(authservice, name)


__credentials_manager__: dict[str, CredentialsManager] = {}


@logtrace
def get_credentials_manager(name=None) -> CredentialsManager:

    creator_item: CredentialsManager = None
    if name is not None:
        creator_item = __credentials_manager__.get(name, None)
    if creator_item is None:
        creator_item = __get_create_instance_from_factory__(instances=__credentials_manager__,
                                                            registration=credentials_manager,
                                                            name=name)
        if creator_item is not None:
            __credentials_manager__[name] = creator_item
    return creator_item


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
    return __get_create_instance_from_factory__(instances=__service_instances__, registration=service, name=identity)


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
