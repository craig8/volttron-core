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
import os

if not os.environ.get('VOLTTRON_SERVER'):
    import importlib
    from pathlib import Path

    from volttron.utils.dynamic_helper import load_dir

    #####################################################################################
    # Step 1:
    # Load all modules within the volttron.client namespace within this package
    #####################################################################################

    # Find the path of the namespace package 'volttron.client'
    client_root = Path(__file__).parent
    # Load the volttron.client package
    load_dir('volttron.client', client_root)

    #####################################################################################
    # Step 2:
    # Load all modules within the volttron namespace within other sources
    #####################################################################################

    # This doesn't reload it, because it's already been loaded.  This allows us
    # access to the paths associated with the other modules.
    volttron_pkg = importlib.import_module("volttron")

    # Loop over paths that aren't in this package
    for pth in filter(lambda p: p != client_root.parent.as_posix, volttron_pkg.__path__):
        load_dir('volttron', Path(pth))

from volttron.client.vip.agent import Agent
from volttron.client.vip.agent.core import Core
from volttron.client.vip.agent.connection import Connection

__all__: list[str] = ['Agent', 'Core', 'Connection']
