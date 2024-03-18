import pytest
from unittest.mock import patch
from pathlib import Path

from volttron.utils.context import EnvironmentalContext


def test_from_env_defaults():
    with pytest.raises(AssertionError):
        context = EnvironmentalContext.from_env()

    with patch('os.environ', {'AGENT_IDENTITY': 'foo', 'AGENT_ADDRESS': 'tcp://127.0.0.1:22916'}):
        context = EnvironmentalContext.from_env()

    assert context.volttron_home == Path("~/.volttron").expanduser().as_posix()
    assert context.launched_by_platform == False
    assert context.identity == 'foo'
    assert context.address == 'tcp://127.0.0.1:22916'
    assert context.data_dir == context.volttron_home + "/agents/foo/data"

    with patch(
            'os.environ', {
                'AGENT_IDENTITY': 'bar',
                'VOLTTRON_HOME': '/tmp/foo',
                '_LAUNCHED_BY_PLATFORM': '1',
                'AGENT_ADDRESS': 'tcp://127.0.0.1:22916'
            }):
        context = EnvironmentalContext.from_env()

    assert context.volttron_home == "/tmp/foo"
    assert context.launched_by_platform == True
    assert context.identity == 'bar'
    assert context.address == 'tcp://127.0.0.1:22916'
    assert context.data_dir == "/tmp/foo/agents/bar/data"


def test_pass_environment_to_context():

    context = EnvironmentalContext.from_env({
        'AGENT_IDENTITY': 'bim',
        'VOLTTRON_HOME': '/tmp/barbim',
        'AGENT_ADDRESS': 'tcp://127.0.0.1:22918'
    })

    assert context.volttron_home == "/tmp/barbim"
    assert context.launched_by_platform == False
    assert context.identity == 'bim'
    assert context.address == 'tcp://127.0.0.1:22918'
    assert context.data_dir == "/tmp/barbim/agents/bim/data"
