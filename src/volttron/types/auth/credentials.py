from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IdentityNotFound(Exception):
    pass


class IdentityAlreadyExists(Exception):
    pass


class Credentials(ABC):
    """
    Interface for credentials objects.

    Implementations of this interface are responsible for providing the credentials required
    for authentication.

    """

    @abstractmethod
    def get_credentials(self) -> Dict[str, Any]:
        """
        Get the credentials.

        :return: A dictionary containing the credentials required for authentication.
        :rtype: Dict[str, Any]
        """
        pass


class ClientCredentials(Credentials):

    def __init__(self, identity: str, **kwargs) -> None:
        self.identity = identity

        for k, v in kwargs.items():
            if not isinstance(k, str):
                raise ValueError(f"Item {k} is not a string. String are required for keys")

        self._credentials = kwargs

    def get_credentials(self) -> Dict[str, Any]:
        return self._credentials


class CredentialStore(ABC):

    @abstractmethod
    def store_credentials(self, identity: str, credentials: Credentials) -> None:
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
    def retrieve_credentials(self, identity: str) -> Credentials:
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
    def delete_credentials(self, identity: str) -> None:
        """
        Delete the credentials for an identity.

        :param identity: The identity to delete credentials for.
        :type identity: str
        :raises: IdentityNotFound: If the identity does not exist, an IdentityNotFound exception MUST be raised.
        """
        pass


class InMemoryCredentialStore(CredentialStore):

    def __init__(self) -> None:
        self._store: Dict[str, Credentials] = {}

    def __len__(self) -> int:
        return len(self._store)

    def store_credentials(self, identity: str, credentials: Credentials) -> None:
        if identity in self._store:
            raise IdentityAlreadyExists(f"Identity: {identity}")
        self._store[identity] = credentials

    def retrieve_credentials(self, identity: str) -> Optional[Any]:
        try:
            return self._store[identity]
        except KeyError:
            raise IdentityNotFound(f"Identity {identity}")

    def delete_credentials(self, identity: str) -> None:
        try:
            del self._store[identity]
        except KeyError:
            raise IdentityNotFound(f"Identity {identity}")