import os
import pytest
from pathlib import Path
from volttron.utils.dynamic_helper import get_module
import importlib


def test_volttron_home_directory_default_case(create_volttron_home_fun_scope: str):
    vhome = Path(create_volttron_home_fun_scope)

    assert vhome.exists()


def test_default_server_options(create_volttron_home_fun_scope: str):
    vhome = Path(create_volttron_home_fun_scope)
    module = importlib.import_module("volttron.server.server_options")
    importlib.reload(module=module)
    from volttron.server.server_options import ServerOptions

    from configparser import ConfigParser
    import socket

    assert ServerOptions
    assert os.environ.get("VOLTTRON_HOME") == ServerOptions.volttron_home.as_posix()
    assert vhome == ServerOptions.volttron_home
    config_path = vhome / "config"
    assert config_path.exists()

    parser = ConfigParser()
    parser.read(str(config_path))

    assert "zmq" == parser.get("volttron", "message-bus")
    assert socket.gethostname() == parser.get("volttron", "instance-name")
    # Can have multiple address entries.
    assert "tcp://127.0.0.1:22916" == parser.get("volttron", "address")
    assert "False" == parser.get("volttron", "agent-isolation-mode")
    assert "volttron.services.config_store" == parser.get("services", "platform.config_store")
    assert "volttron.services.control" == parser.get("services", "platform.control")
    assert "volttron.services.health" == parser.get("services", "platform.health")


def test_server_options_multiple_addresses(create_volttron_home_fun_scope: str):
    vhome = Path(create_volttron_home_fun_scope)
    config = vhome / "config"
    with open(config, "w") as fp:
        fp.write("[volttron]\n")
        fp.write("message-bus = nanomsg\n")
        fp.write("instance-name = nanomsg-volttron-home\n")
        fp.write("address = tcp://127.0.0.1:22916\n")
        fp.write("address = tcp://127.0.0.2:22916\n")
    module = importlib.import_module("volttron.server.server_options")
    importlib.reload(module=module)
    from volttron.server.server_options import ServerOptions

    assert ["tcp://127.0.0.1:22916", "tcp://127.0.0.2:22916"] == ServerOptions.address

    ServerOptions.store(config)

    again = ServerOptions.from_file(config)

    assert ["tcp://127.0.0.1:22916", "tcp://127.0.0.2:22916"] == again.address
