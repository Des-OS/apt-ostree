"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

from apt_ostree.cmd.shell import cli
from apt_ostree.tests import base
from click.testing import CliRunner


class TestRepoCLI(base.TestCase):

    def test_repo_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["repo", "--help"])
        assert result.exit_code == 0
