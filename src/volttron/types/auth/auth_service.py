from abc import ABC, abstractmethod
from typing import Optional

from volttron.server.server_options import ServerOptions
from volttron.types import Identity
from volttron.types.auth.auth_credentials import (Credentials, CredentialsCreator, CredentialsStore)


class Authorizer(ABC):

    # def __init__(*, credentials_rules_map: any, **kwargs):
    #     ...
    @abstractmethod
    def is_authorized(self, *, role: str, action: str, resource: any, **kwargs) -> bool:
        ...


class Authenticator(ABC):

    @abstractmethod
    def authenticate(self, *, credentials: Credentials, address: str, domain: Optional[str] = None) -> bool:
        ...


class AuthorizationManager(ABC):

    @abstractmethod
    def create(self, *, role: str, action: str, resource: any, **kwargs) -> any:
        ...

    @abstractmethod
    def delete(self, *, role: str, action: str, resource: any, **kwargs) -> any:
        ...

    @abstractmethod
    def getall(self) -> list:
        ...


class AuthService(ABC):

    @abstractmethod
    def authenticate(domain: str, address: str, credentials: Credentials) -> Identity:
        ...

    @abstractmethod
    def is_authorized(credentials: Credentials, action: str, resource: str, **kwargs) -> bool:
        ...

    @abstractmethod
    def add_credentials(credentials: Credentials):
        ...

    @abstractmethod
    def remove_credentials(credentials: Credentials):
        ...

    @abstractmethod
    def is_credentials(identity: str) -> bool:
        ...

    @abstractmethod
    def has_credentials_for(identity: str) -> bool:
        ...

    @abstractmethod
    def add_role(role: str) -> None:
        ...

    @abstractmethod
    def remove_role(role: str) -> None:
        ...

    @abstractmethod
    def is_role(role: str) -> bool:
        ...

    # def add_credential_to_role(credential: Credentials, role: str) -> None:
    #     ...

    # def remove_credential_from_role(credential: Credentials, role: str) -> None:
    #     ...

    # def add_capability(name: str, value: str | list | dict, role: str = None, credential: Credentials = None) -> None:
    #     ...

    # def is_capability(name: str):
    #     ...

    # def remove_capability(name: str, role: str, credential: Credentials = None) -> None:
    #     ...
