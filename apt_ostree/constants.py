"""
Copyright (c) 2023-2025 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

VERSION = "0.1"

# packages to exclude from systemd-tmpfiles check.
excluded_packages = [
    "ucf",
    "base-files",
    "systemd",
    "init-system-helpers",
    "dbus",
    "policykit-1",
    "polkitd",
    "debconf"
]

# STX constants
STX_CONFIG_COMPLETE_FLAG = "/etc/platform/.initial_config_complete"
STX_BUILD_INFO_FILE = "/etc/build.info"
STX_KEYWORDS = ["stx", "starlingx", "wrcp"]
