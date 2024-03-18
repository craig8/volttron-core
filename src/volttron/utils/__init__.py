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
"""The volttron.utils package contains generic utilities for handling json, storing configurations math
libraries...and more. """

import logging
from pathlib import Path
from typing import List

import yaml

from volttron.utils.commands import (execute_command, is_volttron_running, isapipe, vip_main,
                                     wait_for_volttron_shutdown, wait_for_volttron_startup)
from volttron.utils.context import ClientContext
from volttron.utils.dynamic_helper import get_class, get_module, get_subclasses
from volttron.utils.file_access import create_file_if_missing
from volttron.utils.identities import is_valid_identity, normalize_identity
from volttron.utils.jsonapi import parse_json_config, strip_comments
from volttron.utils.logs import log_to_file, logtrace, setup_logging
from volttron.utils.messagebus import store_message_bus_config
from volttron.utils.time import (fix_sqlite3_datetime, format_timestamp, get_aware_utc_now, get_utc_seconds_from_epoch,
                                 parse_timestamp_string, process_timestamp)
from volttron.utils.version import get_version

_log = logging.getLogger(__name__)


def load_config(config_path):
    """Load a JSON-encoded configuration file."""
    if not config_path or not Path(config_path).exists():
        raise ValueError("Invalid config_path sent to function.")

    # First attempt parsing the file with a yaml parser (allows comments natively)
    # Then if that fails we fallback to our modified json parser.
    try:
        with open(config_path) as f:
            return yaml.safe_load(f.read())
    except yaml.YAMLError as e:
        try:
            with open(config_path) as f:
                return parse_json_config(f.read())
        except Exception as e:
            _log.error("Problem parsing agent configuration")
            raise


def update_kwargs_with_config(kwargs, config):
    """
    Loads the user defined configurations into kwargs and converts any dash/hyphen in config variables into underscores
    :param kwargs: kwargs to be updated
    :param config: dictionary of user/agent configuration
    """

    for k, v in config.items():
        kwargs[k.replace("-", "_")] = v


__all__: List[str] = [
    "update_kwargs_with_config", "load_config", "parse_json_config", "get_hostname", "log_to_file", "strip_comments",
    "setup_logging", "serialize_frames", "is_valid_identity", "isapipe", "is_volttron_running",
    "create_file_if_missing", "wait_for_volttron_shutdown", "process_timestamp", "parse_timestamp_string",
    "execute_command", "get_version", "get_aware_utc_now", "get_utc_seconds_from_epoch", "get_address",
    "deserialize_frames", "wait_for_volttron_startup", "normalize_identity", "ClientContext", "format_timestamp",
    "store_message_bus_config", "fix_sqlite3_datetime", "vip_main", "get_module", "get_class", "get_subclasses",
    "logtrace"
]
