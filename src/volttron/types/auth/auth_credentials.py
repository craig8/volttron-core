from __future__ import annotations    # Allows reference to current class

from dataclasses import dataclass
from typing import Protocol


class IdentityNotFound(Exception):
    pass


class IdentityAlreadyExists(Exception):
    pass


class InvalidCredentials(Exception):
    pass


@dataclass(frozen=True)
class Credentials:
    identity: str

    def create(*, identity: str) -> Credentials:
        return Credentials(identity=identity)


@dataclass(frozen=True)
class PKICredentials(Credentials):
    publickey: str
    secretkey: str

    def create(*, identity: str, publickey: str, secretkey: str) -> PKICredentials:
        return PKICredentials(identity=identity, publickey=publickey, secretkey=secretkey)


class CredentialsStore(Protocol):

    def store_credentials(identity: str, credential: list[Credentials]) -> None:
        """
        Store credentials for an identity.

        :param identity: The identity to store credentials for.
        :type identity: str
        :param credentials: The credentials to store.
        :type credentials: Any
        :raises: IdentityAlreadyExists: If the identity alredy exists, an IdentityAlreadyExists exception MUST be raised.
        """
        ...

    def retrieve_credentials(identity: str) -> Credentials:
        """
        Retrieve the credentials for an identity.

        :param identity: The identity to retrieve credentials for.
        :type identity: str
        :return: The stored credentials.
        :rtype: Credentials
        :raises: IdentityNotFound: If the identity does not exist, an IdentityNotFound exception MUST be raised.
        """
        ...

    def delete_credentials(identity: str) -> None:
        """
        Delete the credentials for an identity.

        :param identity: The identity to delete credentials for.
        :type identity: str
        :raises: IdentityNotFound: If the identity does not exist, an IdentityNotFound exception MUST be raised.
        """
        ...
