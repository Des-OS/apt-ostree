"""
Copyright (c) 2023 Wind River Systems, Inc.
created by Ivan Ucherdzhiev
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


@click.command(help="Pull branch from local parent repo to local child repo.")
@pass_state_context
@repo_option
@branch_option
@click.option(
    "--child",
    help="Parrent repo to pull from",
)
@gpg_key_option
def pull_local(state,
           repo,
           branch,
           child,
           gpg_key):
    try:
        Compose(state).pull_local(
            child
        )
    except KeyboardInterrupt:
        click.secho("\n" + ("Exiting at your request."))
        sys.exit(130)
    except BrokenPipeError:
        sys.exit()
    except OSError as error:
        if error.errno == errno.ENOSPC:
            sys.exit("error - No space left on device.")
