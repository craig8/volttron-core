import os
from pathlib import Path
import shutil
import sys
import tempfile
import importlib
import pytest

from volttron.types.message_bus import MessageBusInterface

# the following assumes that the testconf.py is in the tests directory.
volttron_src_path = Path(__file__).resolve().parent.parent.joinpath("src")

assert volttron_src_path.exists()

print(sys.path)
if str(volttron_src_path) not in sys.path:
    print(f"Adding source path {volttron_src_path}")
    sys.path.insert(0, str(volttron_src_path))

from fixtures import *
from volttroncorefixtures.nanobackend import *
import pytest


@pytest.fixture
def nanomsg_volttron_home(create_volttron_home_fun_scope: str):
    """
    Creates a volttron home directory with nanomsg as the message bus.
    :return:
    """
    vhome = Path(create_volttron_home_fun_scope)
    config_path = Path(vhome).joinpath("config")
    config_path.touch()
    with open(config_path, "w") as fp:
        fp.write("[volttron]\n")
        fp.write("message-bus = nanomsg\n")
        fp.write("instance-name = nanomsg-volttron-home\n")
        fp.write("address = tcp://127.0.0.1:2044\n")

    yield vhome


@pytest.fixture
def start_message_bus(nanomsg_volttron_home) -> MessageBusInterface:
    module = importlib.import_module("volttron.server.server_options")
    importlib.reload(module=module)
    from volttroncorefixtures.nanobackend import NanoMsgMessageBus
    #nano_msg_bus = NanoMsgMessageBus()
    from volttron.server.server_options import ServerOptions, ServerRuntime

    runtime = ServerRuntime(ServerOptions)

    yield runtime.start_messagebus()

    runtime.shutdown_messagebus()
