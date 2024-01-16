from abc import ABC, abstractmethod
from volttron.types.auth.credentials import Credentials


class AuthServiceProtocol(ABC):

    @abstractmethod
    def is_authorized(credentials: Credentials, action: str, resource: str) -> bool:
        pass

    @abstractmethod
    def register_Credential(credentials: Credentials):
        pass

    @abstractmethod
    def is_authorized(credentials: Credentials, action: str, resource: str) -> bool:
        pass

    @abstractmethod
    def register_Credential(credentials: Credentials) -> bool:
        pass

    @abstractmethod
    def add_role(role: str) -> None:
        pass

    @abstractmethod
    def remove_role(role: str) -> None:
        pass

    @abstractmethod
    def add_credential_to_role(credential: Credentials, group: str) -> None:
        pass

    @abstractmethod
    def remove_credential_from_role(credential: Credentials, group: str) -> None:
        pass

    @abstractmethod
    def add_capability(name: str,
                       value: str | list | dict,
                       role: str = None,
                       credential: Credentials = None) -> None:
        pass

    @abstractmethod
    def remove_capability(name: str, role: str, credential: Credentials = None) -> None:
        pass
