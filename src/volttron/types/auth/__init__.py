from abc import ABC, abstractmethod

class AuthServiceProtocol(ABC):
    
    @abstractmethod
    def is_authorized(credentials: Credentials, action: str, resource: str) -> bool:
        pass
    
    @abstractmethod
    def register_credentials(credentials: Credentials)
        pass
    
    @abstractmethod
    def is_authorized(credentials: Credentials, action: str, resource: str) -> bool:
        pass
    
    @abstractmethod
    def register_credentials(credentials: Credentials) -> bool:
        pass
    
    @abstractmethod
    def add_role(role: str) -> None:
        pass
    
    @abstractmethod
    def remove_role(role: str) -> None:
        pass
    
    @abstractmethod
    def add_credential_to_role(credentials: Credentials, group: str) -> None:
        pass
    
    @abstractmethod
    def remove_credential_from_role(credentials: Credentials, group: str) -> None:
        pass
    
    @abstractmethod
    def add_capability(name: str, value: str | List | Dict, role: str = None, credentials: Credentials = None) -> None:
        pass
    
    @abstractmethod
    def remove_capability(name: str, role: str, credentials: Credentials = None) -> None:
        pass
        
    