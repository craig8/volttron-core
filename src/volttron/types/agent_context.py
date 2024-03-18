import functools
from dataclasses import dataclass, field

from volttron.types.auth.auth_credentials import Credentials


@dataclass
class AgentOptions:
    address: str = None
    heartbeat_autostart: bool = True
    heartbeat_period: int = 60
    volttron_home: str = None
    agent_uuid: str = None
    enable_store: bool = True
    reconnect_interval: int = None
    version: str = "0.1"
    volttron_central_address: str = None,
    volttron_central_instance_name: str = None,
    tag_vip_id: str = None,
    tag_refresh_interval: int = -1
    custom_options: dict[str, any] = field(default_factory=dict)


@dataclass
class AgentContext:
    credentials: Credentials
    address: str | list[str]
    options: AgentOptions = field(default_factory=lambda: AgentOptions())

    def __post_init__(self):
        # if address is set on the options then use it otherwise use the
        # adddress set on the context.
        if self.options.address is not None:
            self.address = self.options.address

    # Use functools rather than try to modify the property of
    # frozen class
    @functools.cached_property
    def address(self):
        if isinstance(self.address, str):
            return [self.address]
        else:
            return self.address
