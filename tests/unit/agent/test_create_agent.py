import os
import sys
from pathlib import Path
from unittest.mock import patch

import gevent

from volttron.client.vip.agent import Agent
from volttron.loader import load_dir
from volttron.server.containers import Frozen
from volttron.types.auth.auth_credentials import Credentials, CredentialsStore
from volttron.types.bases import AgentStarter, ConnectionFactory


@patch.dict('os.environ', {'AGENT_IDENTITY': "test-agent", "AGENT_ADDRESS": "tcp://127.0.0.1:22916"})
def test_create_agent():
    load_dir("corefixtures", Path("/home/os2204/repos/volttron-core/tests/corefixtures"))
    credentials = Credentials(identity="test-agent")
    agent = Agent(credentials=credentials)
    assert agent
    assert agent.vip
    assert agent.core
    assert agent.vip.rpc
    # TODO: Need to figure out pubsub
    #assert agent.vip.pubsub
    assert agent.vip.config
    assert agent.vip.health
    # TODO: Do we enable web here?
    # assert agent.vip.web


def test_vip_main():
    from volttron.client.vip.agent import Agent

    agent_config = Path("/tmp/blank_config")
    agent_config.write_text("{}")

    with patch.dict(os.environ, {"_LAUNCHED_BY_PLATFORM": "1", "AGENT_CONFIG": agent_config.as_posix()}):
        from volttron.utils.commands import vip_main

        #vip_main(agent_class=Agent, identity="test-agent")

        spawned = gevent.spawn(vip_main, agent_class=Agent, identity="test-agent")
        gevent.sleep(1)
        assert spawned.started
        spawned.kill()
        spawned.join()

    agent_config.unlink()


if __name__ == '__main__':
    import pytest

    pytest.main()
