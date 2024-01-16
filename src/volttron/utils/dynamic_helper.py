from __future__ import annotations

import importlib
import inspect
import logging
import sys
from types import ModuleType
from typing import List, Type
from pathlib import Path

from volttron.types.decorators import logtrace

__all__: List[str] = ["get_module", "get_class", "get_subclasses", "load_dir"]

_log = logging.getLogger(__name__)


@logtrace
def load_dir(package: str, pth: Path):
    """
    Recursively loads all modules within a directory.

    :param package: The package name.
    :type package: str
    :param pth: The path to the directory.
    :type pth: :class:`pathlib.Path`

    This function recursively loads all modules within the specified directory. It iterates
    over the files and subdirectories in the directory, imports each module, and loads any
    subdirectories as sub-packages.

    If a file is a Python source file (`.py`), it is imported as a module. If a file is a
    directory, it is loaded as a sub-package.

    Example usage::

        load_dir('volttron', Path('/path/to/directory'))

    .. note::
        This function does not load compiled Python files (`.pyc`) or files in
        the `__pycache__` directory.

    .. warning::
        Be cautious when using this function, as it imports and loads all modules within a
        directory, which may have unintended side effects.
    """

    # Find the caller of this function
    caller_module = inspect.currentframe().f_back.f_globals["__name__"]

    get_mod_name = lambda pth: pth.name if pth.is_dir() else pth.stem

    print("BEFORE")
    before = set(globals().keys())
    print(before)
    # for k in list(globals().keys()):
    #     print(k)
    # We only want to load from py files rather than pyc files
    # so filter
    for p in filter(lambda x: x.name != '__pycache__', pth.iterdir()):

        new_package = f"{package}.{get_mod_name(p)}"
        #importlib.import_module(new_package)
        # print("AFTER")
        # for k in list(globals().keys()):
        #     print(k)

        if new_package.endswith("__init__"):
            print(f"Skipping {new_package}")
            continue

        if f"{caller_module}.__init__" == new_package:
            print(f"Skipping {new_package}")
            continue
        #print(globals())
        if new_package not in globals():
            print(f"Loading {new_package}")
            try:
                globals()[new_package] = importlib.import_module(new_package)
            except ImportError:
                pass
            after = set(globals().keys())
            print("After import")
            print(before - after)
            # print("AFTER!!!!")
            # for k in list(globals().keys()):
            #     print(k)

            #assert new_package in globals()
            if p.is_dir():
                load_dir(new_package, p)


def get_module(module: str) -> ModuleType:
    """Returns a dynamically loaded module. If not found on pythonpath, then raise a ModuleNotFound error.
    This method is a wrapper around Python's builtin function, importlib.import_module(...).
    See https://docs.python.org/3/library/importlib.html#importlib.import_module

    :param module: The name argument specifies what module to import in absolute or relative terms (e.g. either pkg.mod or ..mod).
        If the name is specified in relative terms, then the package argument must be set to the name of the package which is to act as the
        anchor for resolving the package name (e.g. import_module('..mod', 'pkg.subpkg') will import pkg.mod).
    :type module: str
    :raises ModuleNotFoundError:
    :return: A module
    :rtype: ModuleType
    """
    try:
        return importlib.import_module(module)
    except ModuleNotFoundError as e:
        _log.debug(f"Module: {module} not found. Make sure it is on the PYTHONPATH")
        raise e


def get_class(module: str | ModuleType, class_name: str) -> Type:
    """Retrieve a Type from a module. If module is a string, attempt to load it via importlib.import_module.
    If not a string, then directly look for a class within the passed module.

    :param module: the path to a module or the actual module
    :type module: str | ModuleType
    :param class_name: the name of the type in the module
    :type class_name: str
    :raises AttributeError:
    :return: Returns the class from the module
    :rtype: Type
    """
    try:
        if isinstance(module, str):
            return getattr(get_module(module), class_name)
        return getattr(module, class_name)
    except AttributeError as e:
        _log.debug(f"Class {class_name} is not defined in {module}.")
        raise e


def get_all_subclasses(cls):
    """
    Recursively finds all subclasses of the current class.
    Like Python's __class__.__subclasses__(), but recursive.
    Returns a list containing all subclasses.

    @type cls: object
    @param cls: A Python class.
    @rtype: list(object)
    @return: A list containing all subclasses.
    """
    result = set()
    path = [cls]
    while path:
        parent = path.pop()
        for child in parent.__subclasses__():
            if not '.' in str(child):
                # In a multi inheritance scenario, __subclasses__()
                # also returns interim-classes that don't have all the
                # methods. With this hack, we skip them.
                continue
            if child not in result:
                result.add(child)
                path.append(child)
    return result


def get_subclasses_of_classpath(path_of_class: str) -> List[Type]:
    """
    Retrieve a list of classes that implement the passed class_path

    Example path_of_class: `volttron.client.vip.agent.core.Core`

    :param path_of_class: Full dotted path of the class
    :type class_path: str
    :return: A list of subclasses of the passed `path_of_class`
    :rtype: List[Type]
    """
    module, class_name = ".".join(path_of_class.split(".")[:-1]), path_of_class.split(".")[-1]
    module = get_module(module)
    klazz = get_class(module, class_name)
    if isinstance(klazz, type):
        try:
            return klazz.__subclasses__()
        except TypeError:
            import gc
            subclasses = []
            for obj in gc.get_objects():
                if isinstance(obj, type) and obj is not klazz:
                    if klazz in obj.__mro__:
                        subclasses.append(obj)
            return subclasses
    else:
        raise TypeError(f"{klazz} is not a class")


def get_subclasses(module: ModuleType | str,
                   parent_class: Type | str,
                   return_all: bool = False) -> List[Type]:
    """Returns a list of subclasses of a specific type. If return_all is set to True,
    returns all subclasses, otherwise return a list with only the first subclass found.

    :param module: A module containing classes
    :type module: ModuleType | str
    :param parent_class: The parent class that could be a parent of classes in the module
    :type parent_class: Type | str
    :param return_all: True if all subclasses are desired; False if only the first subclass. Defaults to False
    :type return_all: bool, optional
    :raises ValueError: Raises ValueError if no subclasses are found.
    :return: A list of sublcasses of a specific type
    :rtype: List
    """
    all_subclasses = []

    if isinstance(module, str):
        module = importlib.import_module(module)

    if isinstance(parent_class, str):
        parent_class = getattr(module, parent_class)

    for c in inspect.getmembers(module, inspect.isclass):
        if parent_class in c[1].__bases__:
            all_subclasses.append(c[1])
            if not return_all:
                break

    if not all_subclasses:
        raise ValueError(f"No subclass of {parent_class} found in {module.__name__}")

    return all_subclasses
