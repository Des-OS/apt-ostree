"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import click

from apt_ostree.constants import VERSION


@click.command(name="version", help="Show version and exit.")
@click.pass_context
def version(ctxt):
    print(VERSION)
