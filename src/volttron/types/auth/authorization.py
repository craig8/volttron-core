from abc import ABC, abstractmethod
from typing import List, Optional, Tuple


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
    def add_permission(self, role: str, credential: str, permission: str) -> None:
        """
        Add a new permission for a specific credential to a role.

        :param role: The name of the role.
        :type role: str

        :param credential: The identifier of the credential.
        :type credential: str

        :param permission: The name of the permission.
        :type permission: str
        """
        pass

    @abstractmethod
    def remove_permission(self, role: str, credential: str, permission: str) -> None:
        """
        Remove an existing permission for a specific credential from a role.

        :param role: The name of the role.
        :type role: str

        :param credential: The identifier of the credential.
        :type credential: str

        :param permission: The name of the permission.
        :type permission: str
        """
        pass

    @abstractmethod
    def check_permission(self, credential: str, permission: str) -> bool:
        """
        Check if a credential has a specific permission.

        :param credential: The identifier of the credential.
        :type credential: str

        :param permission: The name of the permission.
        :type permission: str

        :return: True if the credential has the permission, False otherwise.
        :rtype: bool
        """
        pass