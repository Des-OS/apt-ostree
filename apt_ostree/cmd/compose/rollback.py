"""
Copyright (c) 2024 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

import errno
import sys

import click

from apt_ostree.cmd.options import branch_option
from apt_ostree.cmd.options import repo_option
from apt_ostree.cmd import pass_state_context
from apt_ostree.compose import Compose


@click.command(
    help="Rollback an ostree commit.")
@pass_state_context
@repo_option
@branch_option
@click.argument(
    "commit",
    nargs=1
)
def rollback(state, repo, branch, commit):
    try:
        Compose(state).rollback(commit)
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
