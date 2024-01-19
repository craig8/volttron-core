from typing import Protocol, runtime_checkable

from volttron.types.auth.auth_credentials import Credentials, CredentialsStore


@runtime_checkable
class AuthorizerProtocol(Protocol):

    def is_authorized(self, role: str, action: str, resource: any, **kwargs) -> bool:
        ...


@runtime_checkable
class AuthenticatorProtocol(Protocol):

    def authenticate(self, credentials: Credentials) -> bool:
        ...


@runtime_checkable
class AuthServiceProtocol(Protocol):

    def initialize(store: CredentialsStore, authorizer: AuthorizerProtocol, authenticator: AuthenticatorProtocol):
        ...

    @staticmethod
    def get_auth_type() -> str:
        ...

    def is_authorized(credentials: Credentials, action: str, resource: str) -> bool:
        ...

    def is_authorized(credentials: Credentials, action: str, resource: str) -> bool:
        ...

    def register_Credential(credentials: Credentials):
        ...

    def is_authorized(credentials: Credentials, action: str, resource: str) -> bool:
        ...

    def register_Credential(credentials: Credentials) -> bool:
        ...

    def add_role(role: str) -> None:
        ...

    def remove_role(role: str) -> None:
        ...

    def add_credential_to_role(credential: Credentials, group: str) -> None:
        ...

    def remove_credential_from_role(credential: Credentials, group: str) -> None:
        ...

    def add_capability(name: str, value: str | list | dict, role: str = None, credential: Credentials = None) -> None:
        ...

    def remove_capability(name: str, role: str, credential: Credentials = None) -> None:
        ...
