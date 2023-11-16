from types import MappingProxyType
from typing import Any, Dict, Optional

import pytest

from volttron.types import (ClientCredentials, Credentials, CredentialStore,
                            IdentityAlreadyExists, IdentityNotFound,
                            InMemoryCredentialStore)
from volttron.types.auth.authentication import Authentication


class UsernamePasswordCredential(ClientCredentials):

    def __init__(self, username: str, password: str):
        super().__init__(identifier=username, username=username, password=password)


@pytest.fixture()
def preloaded_store() -> InMemoryCredentialStore:
    store = InMemoryCredentialStore()
    # Create credentials
    alpha = UsernamePasswordCredential("alpha", "beta")
    beta = UsernamePasswordCredential("beta", "gamma")
    store.store_credentials("alpha", alpha)
    store.store_credentials("beta", beta)

    yield store

    store.delete_credentials("alpha")
    store.delete_credentials("beta")


def test_username_password_credentials():
    u = UsernamePasswordCredential("foo", "bar")

    creds = u.get_credentials()

    assert "foo" == creds["username"]
    assert "bar" == creds["password"]


def test_can_store_retreive_credentials():
    store = InMemoryCredentialStore()
    # Create credentials
    alpha = UsernamePasswordCredential("alpha", "beta")
    beta = UsernamePasswordCredential("beta", "gamma")

    # Store creds
    store.store_credentials("alpha", alpha)
    store.store_credentials("beta", beta)
    assert 2 == len(store)

    # Retreive based one identity
    result: Credentials = store.retrieve_credentials("alpha")
    assert 'alpha' == result.get_credentials()["username"]
    assert 'beta' == result.get_credentials()["password"]

    result: Credentials = store.retrieve_credentials("beta")
    assert 'beta' == result.get_credentials()['username']
    assert 'gamma' == result.get_credentials()['password']

    store.delete_credentials('alpha')
    assert 1 == len(store)

    with pytest.raises(IdentityNotFound):
        result: Credentials = store.retrieve_credentials("alpha")

    with pytest.raises(IdentityNotFound):
        result: Credentials = store.delete_credentials("alpha")

    with pytest.raises(IdentityAlreadyExists):
        store.store_credentials("beta", beta)


def test_authenticate(preloaded_store):
    pass