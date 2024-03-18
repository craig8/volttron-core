import os
import pytest
from pathlib import Path
from volttron.utils.dynamic_helper import get_module
from volttron_testutils import make_volttron_home_func_scope
import importlib


def test_volttron_home_directory_default_case(make_volttron_home_func_scope: str):
    vhome = Path(os.environ.get("VOLTTRON_HOME", ""))

    assert vhome.exists()


def test_default_server_options(make_volttron_home_func_scope):
    vhome = Path(os.environ.get("VOLTTRON_HOME", ""))
    module = importlib.import_module("volttron.server.server_options")
    importlib.reload(module=module)
    from volttron.server.server_options import ServerOptions

    from configparser import ConfigParser
    import socket

    opts = ServerOptions()
    opts1 = ServerOptions()
    assert id(opts) == id(opts1)

    assert os.environ.get("VOLTTRON_HOME") == opts.volttron_home.as_posix()
    assert vhome == ServerOptions.volttron_home
    config_path = vhome / "config"
    assert not config_path.exists()

    opts.from_file()

    #opts.store(config_path)
    #ServerOptions.from_file()
    assert config_path.exists()

    parser = ConfigParser()
    parser.read(str(config_path))

    assert "zmq" == parser.get("volttron", "messagebus")
    assert socket.gethostname() == parser.get("volttron", "instance-name")
    # Can have multiple address entries.
    assert "tcp://127.0.0.1:22916" == parser.get("volttron", "address")
    assert "False" == parser.get("volttron", "agent-isolation-mode")
    # TODO services here!
    #assert "volttron.services.config_store" == parser.get("services", "platform.config_store")
    #assert "volttron.services.control" == parser.get("services", "platform.control")
    #assert "volttron.services.health" == parser.get("services", "platform.health")


def test_server_options_multiple_addresses(make_volttron_home_func_scope):
    vhome = os.environ.get("VOLTTRON_HOME", "")
    assert vhome
    config = Path(vhome) / "config"
    with open(config, "w") as fp:
        fp.write("[volttron]\n")
        fp.write("message-bus = nanomsg\n")
        fp.write("instance-name = nanomsg-volttron-home\n")
        fp.write("address = tcp://127.0.0.1:22916\n")
        fp.write("address = tcp://127.0.0.2:22916\n")
    module = importlib.import_module("volttron.server.server_options")
    importlib.reload(module=module)
    from volttron.server.server_options import ServerOptions

    opts = ServerOptions.from_file()

    assert ["tcp://127.0.0.1:22916", "tcp://127.0.0.2:22916"] == opts.address

    opts.store(config)

    again = opts.from_file(config)

    assert ["tcp://127.0.0.1:22916", "tcp://127.0.0.2:22916"] == again.address
