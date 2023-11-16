from abc import ABC, abstractmethod
from typing import Any, Dict

from .credentials import Credentials, PublicCredentials


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

    @abstractmethod
    def add_credentials(self, public_credentials: PublicCredentials):
        """
        Add a credential to the authentication store.  
        
        This method should be able to persist the public_credentials to a store such that the authenticate
        method will be able to authenticate based upon a public/private credential pair.

        :param credentials: The credentials to use for authentication.
        :type credentials: PublicCredentials
        """
        pass

    @abstractmethod
    def remove_credentials(self, idenitifier: str):
        """
        Remove credentials from the credential store.
        
        This method should be able to remove an entry in the credentials such that the authenticate
        method will NOT be able to authenticate based upon a public/private credential pair for the 
        given idenitifier.

        :param idenitifier: The identifier to use for authentication.
        :type idenitifier: str
        """
        pass