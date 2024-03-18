from corefixtures.simplecoreandconnection import SimpleConnectionFactory, SimpleCoreBuilder
from volttron.client.vip.agent import Core
from volttron.types.auth.auth_credentials import Credentials
import gevent
import logging

from volttron.types.factories import ConnectionBuilder, CoreBuilder

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)


def test_can_build_core_class():

    creds = Credentials(identity="test-agent")
    factory = SimpleConnectionFactory(address="tcp://127.0.0.1:22916")
    assert isinstance(factory, ConnectionBuilder)

    # connection = factory.build(credentials=creds)
    # assert isinstance(connection, Connection)

    core = Core(None, creds, factory)

    assert core.identity == creds.identity
    assert core._connection is not None
    assert core.get_connected() is False


def test_can_run_core():
    creds = Credentials(identity="test-agent")
    factory = SimpleConnectionFactory(address="tcp://127.0.0.1:22916")

    core = SimpleCoreBuilder.SimplisticCore(None, creds, factory)
    #core = Core(None, creds, factory)
    core.setup()

    timeout = 3
    event = gevent.event.Event()
    task = gevent.spawn(core.run, event)
    with gevent.Timeout(timeout):
        event.wait()

    assert core.connected is True
    assert core.get_connected() is True

    core.stop()
