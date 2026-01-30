"""
Copyright (c) 2023-2024 Wind River Systems, Inc.

SPDX-License-Identifier: Apache-2.0

"""
import logging
import subprocess
import sys
import textwrap

import click
from rich.console import Console
from rich.table import Table

from apt_ostree.deploy import Deploy
from apt_ostree.ostree import Ostree
from apt_ostree import utils


class Repo:
    def __init__(self, state):
        self.console = Console()
        self.logging = logging.getLogger(__name__)
        self.state = state
        self.repo = self.state.feed
        self.deploy = Deploy(self.state)
        self.ostree = Ostree(self.state)
        self.console = Console()

        self.label = "StarlingX project udpates."
        self.arch = "amd64"
        self.description = "Apt repository for StarlingX updates."

    def init(self):
        """Create a Debian archive from scratch."""
        self.logging.info("Creating Debian package archive.")
        self.repo = self.repo.joinpath("conf")
        if not self.repo.exists():
            self.logging.info("Creating package feed directory.")
            self.repo.mkdir(parents=True, exist_ok=True)

        config = self.repo.joinpath("distributions")
        if config.exists():
            self.logging.info("Found existing reprepro configuration.")
            sys.exit(1)
        else:
            self.logging.info("Creating reprepro configuration.")
            try:
                config.write_text(
                    textwrap.dedent(f"""\
                    Origin: {self.state.origin}
                    Label: {self.label}
                    Codename: {self.state.release}
                    Architectures: amd64
                    Components: {self.state.origin}
                    Description: {self.description}
                    """)
                )
            except Exception as e:
                self.logging.error("Error writing distributions \
                                    config file: %s" % str(e))
            options = self.repo.joinpath("options")
            if not options.exists():
                options.write_text(
                    textwrap.dedent(f"""\
                    basedir {self.repo}
                    """)
                )

    def add(self):
        """Add Debian package(s) to a component."""
        config = self.repo.joinpath("conf/distributions")
        component = self.state.component or self.state.origin

        utils.check_and_append_component(config, component)

        for pkg in self.state.packages:
            self.logging.info(
                f"Adding {pkg} to component {component}.")
            r = utils.run_command(
                ["reprepro", "-b", str(self.repo), "-C", component,
                 "includedeb", self.state.release, pkg])
            if r.returncode == 0:
                self.logging.info(
                    f"Successfully added {pkg} to component {component}\n")
            else:
                self.logging.error(
                    f"Failed to add {pkg} to component {component}\n")

    def show(self):
        """Display a table of packages in the archive."""
        component = self.state.component or self.state.origin

        r = utils.run_command(
            ["reprepro", "-b", str(self.repo),
             "-C", component,
             "list", self.state.release],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        # Repo not configured yet
        if r.returncode == 254:
            sys.exit(1)
        if r.returncode != 0:
            click.secho(r.stdout.decode("utf-8"))
        if r.stdout and "Exiting" in r.stdout.decode("utf-8"):
            click.secho(r.stdout.decode("utf-8"))
        else:
            table = Table(box=None)
            table.add_column("Package")
            table.add_column("Version")
            table.add_column("Release")
            table.add_column("Origin")
            table.add_column("Architecture")

            for line in r.stdout.decode("utf-8").splitlines():
                (metadata, package, version) = line.split()
                (suite, origin, arch) = metadata.split("|")
                table.add_row(package, version, suite, origin, arch[:-1])

            self.console.print(table)

    def remove(self):
        """Remove Debian packages or a component."""

        component = self.state.component or self.state.origin

        if self.state.packages:
            # delete package by package
            for pkg in self.state.packages:
                self.logging.info(f"Removing {pkg}.")
                r = utils.run_command(
                    ["reprepro", "-b", str(self.repo), "-C", component,
                     "remove", self.state.release, pkg],
                    check=True)
                if r.returncode == 0:
                    self.logging.info(
                        f"Removed {pkg} from component {component}\n")
                else:
                    self.logging.error(
                        f"Failed to remove {pkg} from component {component}\n")
        else:
            # delete the entire component
            config = self.repo.joinpath("conf/distributions")

            if utils.remove_component_from_config(config, component):
                dist_component = self.repo.joinpath(
                    f"dists/bullseye/{component}")
                pool_component = self.repo.joinpath(f"pool/{component}")

                try:
                    utils.run_command(
                        ["rm", "-r", str(dist_component)],
                        check=True)
                except Exception:
                    self.logging.info(f"Could not remove {dist_component},"
                                      " skipping anyway\n")
                try:
                    utils.run_command(
                        ["rm", "-r", str(pool_component)],
                        check=True)
                except Exception:
                    self.logging.info(f"Could not remove {pool_component},"
                                      " skipping anyway\n")
                try:
                    utils.run_command(
                        ["reprepro", "-b", str(self.repo),
                         "--delete", "clearvanished"],
                        check=True)
                except Exception:
                    self.logging.info("Could not run reprepro clearvanished,"
                                      " skipping anyway\n")
                try:
                    utils.run_command(
                        ["reprepro", "-b", str(self.repo),
                         "deleteunreferenced"],
                        check=True)
                except Exception:
                    self.logging.info("Could not run reprepro "
                                      "deleteunreferenced, skipping anyway\n")

                self.logging.info(f"Removed component {component}\n")
            else:
                self.logging.error(f"Failed to remove component {component}\n")

    def disable_repo(self):
        """Disable Debian feed via apt-add-repository."""
        rootfs = self.deploy.get_sysroot()
        branch = self.ostree.get_branch()
        self.deploy.prestaging(rootfs)
        self.logging.info(
            "Disablng Debian package feeds.")
        cmd = [
            "apt-add-repository",
            "-r", "-y", "-n",
            self.state.sources
        ]
        r = utils.run_sandbox_command(
            cmd,
            rootfs,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        if r.returncode != 0:
            self.logging.error("Failed to disable package feed.")
            sys.exit(1)
        self.logging.info(
            f"Successfully disabled  \"{self.state.sources}\".")
        self.deploy.poststaging(rootfs)

        self.logging.info(f"Committing to {branch} to repo.")
        r = self.ostree.ostree_commit(
            root=str(rootfs),
            branch=branch,
            repo=self.state.repo,
            subject="Disabled package feed.",
            msg=f"Disabled {self.state.sources}",
        )
        if r.returncode != 0:
            self.logging.error("Failed to commit to repository.")
        else:
            self.ostree.ostree_summary_update(self.state.repo)
        self.deploy.cleanup(str(rootfs))

    def add_repo(self):
        """Enable Debian feed via apt-add-repository."""
        rootfs = self.deploy.get_sysroot()
        branch = self.ostree.get_branch()
        self.deploy.prestaging(rootfs)
        self.logging.info(
            "Enabling addtional Debian package feeds.")
        cmd = [
            "apt-add-repository",
            "-y", "-n",
            self.state.sources
        ]
        r = utils.run_sandbox_command(
            cmd,
            rootfs,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        if r.returncode != 0:
            self.logging.error("Failed to add package feed.")
            sys.exit(1)
        self.logging.info(
            f"Successfully added \"{self.state.sources}\".")
        self.deploy.poststaging(rootfs)

        self.logging.info(f"Committing to {branch} to repo.")
        r = self.ostree.ostree_commit(
            root=str(rootfs),
            branch=branch,
            repo=self.state.repo,
            subject="Enable package feed.",
            msg=f"Enabled {self.state.sources}",
        )
        if r.returncode != 0:
            self.logging.error("Failed to commit to repository")
        else:
            self.ostree.ostree_summary_update(self.state.repo)
        self.deploy.cleanup(str(rootfs))
