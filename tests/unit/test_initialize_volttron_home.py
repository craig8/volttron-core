import os
import pytest
from pathlib import Path
from volttron.utils.dynamic_helper import get_module

# We have tests that will only pass if the message bus is
# on the path.
try:
    message_bus = get_module("volttron.messagebus")
except ModuleNotFoundError:
    message_bus = None


def test_volttron_home_directory_default_case(create_volttron_home_fun_scope: str):
    vhome = Path(create_volttron_home_fun_scope)

    assert vhome.exists()


@pytest.mark.skipif(message_bus == None, reason="No messagebus has been loaded in scope.")
def test_default_server_options(create_volttron_home_fun_scope: str):
    vhome = Path(create_volttron_home_fun_scope)

    from volttron.server.server_options import ServerOptions
    from configparser import ConfigParser
    import socket

    assert ServerOptions
    assert vhome == ServerOptions.volttron_home
    config_path = vhome / "config"
    assert config_path.exists()

    parser = ConfigParser()
    parser.read(str(config_path))

    assert "zmq" == parser.get("volttron", "message-bus")
    assert socket.gethostname() == parser.get("volttron", "instance-name")
    assert "tcp://127.0.0.1:22916" == parser.get("volttron", "address")
    assert "False" == parser.get("volttron", "agent-isolation-mode")
    assert "volttron.services.config_store" == parser.get("services", "platform.config_store")
    assert "volttron.services.control" == parser.get("services", "platform.control")
    assert "volttron.services.health" == parser.get("services", "platform.health")
