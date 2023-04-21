from abc import ABC, abstractmethod
from typing import Any, Dict

from .credentials import Credentials


class AuthenticationError(Exception):
    pass


class Authentication(ABC):
    """
    Interface for authentication objects.

    Implementations of this interface are responsible for authenticating a set of credentials
    to determine if they are valid and can be used to access a resource.

    """

    @abstractmethod
    def authenticate(self, credentials: Credentials) -> bool:
        """
        Authenticate the provided credentials.

        :param credentials: The credentials to use for authentication.
        :type credentials: Credentials

        :return: True if the credentials are valid, False otherwise.
        :rtype: bool
        """
        pass
