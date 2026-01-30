"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""


class AptError(Exception):
    """Base class for apt-ostree exceptions."""

    def __init__(self, message=None):
        super(AptError, self).__init__(message)
        self.message = message

    def __str__(self):
        return self.message or ""


class ConfigError(AptError):
    """Configuration file error."""
    pass


class CommandError(AptError):
    """Command execution error."""
    pass


class PackageError(AptError):
    """Package operation error."""
    pass
