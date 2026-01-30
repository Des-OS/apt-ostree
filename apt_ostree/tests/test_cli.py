"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

from apt_ostree.cmd.shell import cli
from apt_ostree.tests import base
from click.testing import CliRunner


class TestAPTCLI(base.TestCase):

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0

    def test_compose(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["compose", "--help"])
        assert result.exit_code == 0

    def test_debug(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--debug", "version"])
        assert result.exit_code == 0
