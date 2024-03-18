import dataclasses
import pytest
from volttron.types import AgentContext, AgentOptions
from volttron.types.auth import Credentials


def test_can_change_options_but_not_address():
    context = AgentContext(credentials=Credentials(identity="foo"),
                           address="tcp://127.0.0.1:22916",
                           options=AgentOptions())
    assert context.options.enable_store
    context.options.enable_store = False
    assert not context.options.enable_store
    # assert not context.options.enable_web
    # context.options.enable_web = True
    # assert context.options.enable_web
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.address = "tcp://127.0.0.2:22916"
