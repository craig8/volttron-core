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

    # print("BEFORE")
    # before = set(globals().keys())
    # print(before)
    # # for k in list(globals().keys()):
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
            # after = set(globals().keys())
            # print("After import")
            # print(before - after)
            # print("AFTER!!!!")
            # for k in list(globals().keys()):
            #     print(k)

            #assert new_package in globals()
            if p.is_dir():
                load_dir(new_package, p)
