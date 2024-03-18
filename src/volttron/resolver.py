import inspect

from volttron.client.decorators import (core_builder, get_connection_builder, get_core_builder)
from volttron.types.auth.auth_credentials import Credentials
from volttron.types.factories import ConnectionBuilder, CoreBuilder

__all__: list[str] = []


def get_credentials_from_store(**kwargs) -> Credentials:

    # TODO: If we have an auth service, then we should use a registered store
    # to get the credentials. If no auth service then we just use the default
    # credentials.

    # Identity must be one of the passed parameters
    if 'identity' not in kwargs:
        raise ValueError('identity must be specified.')

    # Returning Default for non-authenticated parameters
    return Credentials.create(identity=kwargs['identity'])
