from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class AuthorizationError(Exception):
    pass


class Authorizer:

    @abstractmethod
    def is_authorized(self, role: str, action: str, resource: any, **kwargs) -> bool:
        pass


class Authorization(ABC):
    """
    Interface for authorization objects.

    Implementations of this interface are responsible for controlling access to a resource
    based on a set of roles and permissions.

    """

    @abstractmethod
    def add_role(self, role: str) -> None:
        """
        Add a new role.

        :param role: The name of the new role.
        :type role: str
        """
        pass

    @abstractmethod
    def remove_role(self, role: str) -> None:
        """
        Remove an existing role.

        :param role: The name of the role to remove.
        :type role: str
        """
        pass

    @abstractmethod
    def assign_role(self, role: str, identifier: str):
        pass

    @abstractmethod
    def unassign_role(self, role: str, identifer: str):
        pass

    @abstractmethod
    def unassign_all_roles(self, identifier: str):
        pass

    @abstractmethod
    def get_permissions(self, role: str = None, identifier: str = None) -> List[str]:
        pass

    @abstractmethod
    def get_roles(self, identifer: str = None) -> List[str]:
        pass

    @abstractmethod
    def add_permission(self, role: str, permission: str, identifier: str = None) -> None:
        """
        Add a new permission for a specific identifier to a role.

        :param role: The name of the role.
        :type role: str

        :param identifier: The identifier of the identifier.
        :type identifier: str

        :param permission: The name of the permission.
        :type permission: str
        """
        pass

    @abstractmethod
    def remove_permission(self, role: str, permission: str) -> None:
        """
        Remove an existing permission for a specific identifier from a role.

        :param role: The name of the role.
        :type role: str

        :param permission: The name of the permission.
        :type permission: str
        """
        pass

    @abstractmethod
    def check_permission(self, permission: str, identifier: str) -> bool:
        """
        Check if a identifier has a specific permission.

        :param identifier: The identifier of the identifier.
        :type identifier: str

        :param permission: The name of the permission.
        :type permission: str

        :return: True if the identifier has the permission, False otherwise.
        :rtype: bool
        """
        pass
