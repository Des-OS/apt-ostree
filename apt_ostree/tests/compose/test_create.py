"""
Copyright (c) 2023 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""

from apt_ostree.cmd.shell import cli
from apt_ostree.tests import base
from click.testing import CliRunner


class TestComposeCLI(base.TestCase):

    def test_compose_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["compose", "--help"])
        assert result.exit_code == 0

    def test_compose_image(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["compose", "image", "--help"])
        assert result.exit_code == 0
