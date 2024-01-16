from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Optional


class IdentityNotFound(Exception):
    pass


class IdentityAlreadyExists(Exception):
    pass


class InvalidCredentials(Exception):
    pass


@dataclass(frozen=True)
class Credentials:
    identity: str


@dataclass(frozen=True)
class PKICredentials(Credentials):
    public: str
    secret: str


class CredentialManager:

    def __init__(self, cred_list: Credential) -> None:
        self._store = InMemoryCredentialStore(cred_list)

    def add(self, credential: Credential):
        self._store.add(credential)

    def remove(self, identity):
        self._store.delete_credential(identity)

    def get(self, identity) -> Credential:
        self._store.retrieve_credential(identity)


class ClientCredential(Credentials):
    pass


# class Credentials(ABC):
#     """
#     Interface for credentials objects.

#     Implementations of this interface are responsible for providing the credentials required
#     for authentication.

#     """

#     @abstractmethod
#     def get_identifier(self) -> str:
#         pass

#     @abstractmethod
#     def get_credentials(self) -> Dict[str, Any]:
#         """
#         Get the credentials.

#         :return: A dictionary containing the credentials required for authentication.
#         :rtype: Dict[str, Any]
#         """
#         pass

#     @staticmethod
#     @abstractmethod
#     def create(identifier: str, **kwargs) -> Credentials:
#         pass

# class PublicCredentials(Credentials):

#     def __init__(self, identifier: str, **kwargs) -> None:
#         self._identifier = identifier
#         self._kwargs = kwargs
#         for k, v in kwargs.items():
#             if not isinstance(k, str):
#                 raise InvalidCredentials(f"Key must be string not {type(k)}")

#     def get_credentials(self) -> Dict[str, Any]:
#         return self._kwargs

#     def get_identifier(self) -> str:
#         return self._identifier

#     @staticmethod
#     def create(identifier: str, **kwargs) -> Credentials:
#         return PublicCredentials(identifier, **kwargs)

# class ClientCredentials(Credentials):

#     def __init__(self, identifier: str, **kwargs) -> None:
#         self._identifier = identifier

#         for k, v in kwargs.items():
#             if not isinstance(k, str):
#                 raise ValueError(f"Item {k} is not a string. String are required for keys")

#         self._credentials = kwargs

#     def get_identifier(self) -> str:
#         return self._identifier

#     def get_credentials(self) -> Dict[str, Any]:
#         return self._credentials


class CredentialStore(ABC):

    @abstractmethod
    def store_credential(self, identity: str, credential: list[Credential]) -> None:
        """
        Store credentials for an identity.

        :param identity: The identity to store credentials for.
        :type identity: str
        :param credentials: The credentials to store.
        :type credentials: Any
        :raises: IdentityAlreadyExists: If the identity alredy exists, an IdentityAlreadyExists exception MUST be raised.
        """
        pass

    @abstractmethod
    def retrieve_credential(self, identity: str) -> Credential:
        """
        Retrieve the credentials for an identity.

        :param identity: The identity to retrieve credentials for.
        :type identity: str
        :return: The stored credentials.
        :rtype: Credentials
        :raises: IdentityNotFound: If the identity does not exist, an IdentityNotFound exception MUST be raised.
        """
        pass

    @abstractmethod
    def delete_credential(self, identity: str) -> None:
        """
        Delete the credentials for an identity.

        :param identity: The identity to delete credentials for.
        :type identity: str
        :raises: IdentityNotFound: If the identity does not exist, an IdentityNotFound exception MUST be raised.
        """
        pass


class InMemoryCredentialStore(CredentialStore):

    def __init__(self, credentials: list[Credential] = None) -> None:
        self._store: dict[str, Credential] = {}
        for cred in credentials:
            self.store_credential(cred.identity, cred)

    def __len__(self) -> int:
        return len(self._store)

    def add(self, credential: Credential) -> None:
        self.store_credential(credential.identity, credential)

    def store_credential(self, identity: str, credential: Credential) -> None:
        if identity in self._store:
            raise IdentityAlreadyExists(f"Identity: {identity}")
        self._store[identity] = credential

    def retrieve_credential(self, identity: str) -> Optional[Any]:
        try:
            return self._store[identity]
        except KeyError:
            raise IdentityNotFound(f"Identity {identity}")

    def delete_credential(self, identity: str) -> None:
        try:
            del self._store[identity]
        except KeyError:
            raise IdentityNotFound(f"Identity {identity}")

    def list(self) -> list[Credential]:
        return [deepcopy(x) for x in self._store.values()]
