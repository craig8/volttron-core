# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Installable Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2022 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}

AUTH = "platform.auth"

VOLTTRON_CENTRAL = "volttron.central"
VOLTTRON_CENTRAL_PLATFORM = "platform.agent"
PLATFORM_AUTH = AUTH
PLATFORM_DRIVER = "platform.driver"
PLATFORM_TOPIC_WATCHER = "platform.topic_watcher"
PLATFORM_SYSMON = "platform.sysmon"
PLATFORM_EMAILER = "platform.emailer"
PLATFORM_HEALTH = "platform.health"
# The PLATFORM_ALERTER known name is now deprecated
PLATFORM_ALERTER = PLATFORM_TOPIC_WATCHER
PLATFORM_HISTORIAN = "platform.historian"
PLATFORM_MARKET_SERVICE = "platform.market"
PLATFORM_TAGGING = "platform.tagging"

ROUTER = ""
CONTROL = "platform.control"
PLATFORM_CONTROL = CONTROL
CONTROL_CONNECTION = "control.connection"
PLATFORM_WEB = "platform.web"
CONFIGURATION_STORE = "platform.config_store"
PLATFORM_CONFIG = CONFIGURATION_STORE
KEY_DISCOVERY = "keydiscovery"
PROXY_ROUTER = "zmq.proxy.router"

ALL_KNOWN_IDENTITIES = sorted((
    ROUTER,
    VOLTTRON_CENTRAL,
    VOLTTRON_CENTRAL_PLATFORM,
    PLATFORM_HISTORIAN,
    PLATFORM_CONFIG,
    CONTROL,
    CONTROL_CONNECTION,
    PLATFORM_WEB,
    AUTH,
    PLATFORM_TOPIC_WATCHER,
    CONFIGURATION_STORE,
    PLATFORM_MARKET_SERVICE,
    PLATFORM_EMAILER,
    PLATFORM_SYSMON,
    PLATFORM_HEALTH,
    KEY_DISCOVERY,
    PROXY_ROUTER,
))

PROCESS_IDENTITIES = sorted((
    AUTH,
    PLATFORM_HEALTH,
    PLATFORM_CONFIG,
    CONTROL,
    PLATFORM_WEB,
    KEY_DISCOVERY,
    PROXY_ROUTER,
))
