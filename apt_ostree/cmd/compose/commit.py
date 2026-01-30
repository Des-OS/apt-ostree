"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import branch_option
from apt_ostree.cmd.options import gpg_key_option
from apt_ostree.cmd.options import repo_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.compose import Compose


@click.command(help="Commit a target path to an OSTree repository.")
@pass_state_context
@repo_option
@click.option(
    "--parent",
    help="Commit with a specific parent",
)
@branch_option
@gpg_key_option
def commit(state,
           repo,
           parent,
           gpg_key,
           branch):
    try:
        Compose(state).commit(
            parent
        )
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
