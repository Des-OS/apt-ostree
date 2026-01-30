"""
Copyright (c) 2023-2024 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import branch_option
from apt_ostree.cmd.options import component_option
from apt_ostree.cmd.options import gpg_key_option
from apt_ostree.cmd.options import packages_option
from apt_ostree.cmd.options import repo_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.packages import Packages


@click.command(
    help="Install Debian package in a target to an OSTree repository.")
@pass_state_context
@branch_option
@repo_option
@click.option(
    "--feed",
    help="Debian package feed",
    nargs=1)
@gpg_key_option
@component_option
@packages_option
def install(state,
            branch,
            repo,
            feed,
            gpg_key,
            component,
            packages):
    try:
        Packages(state).install(packages, feed, component)
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
